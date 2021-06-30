__version__ = "0.0.1"

import sqlparse
import os
import re
import copy


def get_cols(sql_statement):
    '''
    :param sql_statement: sql-parsed sql statement
    :return: column_dictionary
    '''
    col_dict = dict()
    sql_identifier_pat = re.compile(r"SELECT (.*?)\s*\n*FROM", re.I | re.DOTALL)
    sql_identifier_list = sql_identifier_pat.findall(str(sql_statement))

    for token in sql_statement.tokens:

        if type(token) == sqlparse.sql.IdentifierList:
            line_pattern = re.compile(',\n')
            token_split = line_pattern.split(str(token))

            if 'row_number()' in token_split:
                token_split.remove('row_number()')

            for token_string in token_split:
                token_string = token_string.strip().replace('\t', '').replace('\n', '')
                token_fmt = token_string.rsplit(' AS ', 1)
                token_fmt1 = token_string.split('.')
                token_fmt2 = token_string.rsplit(' ', 1)

                if len(token_fmt) > 1:
                    col_dict[token_fmt[1].strip()] = token_fmt[0].strip()

                elif (' AS ' not in token_string) and ('*' not in token_string):
                    if len(token_fmt2) > 1:
                        col_dict[token_fmt2[1].strip()] = token_fmt2[0].strip()
                    elif len(token_fmt1) > 1:
                        col_dict[token_fmt1[1].strip()] = token_string.strip()
                    elif ('.' not in token_string):
                        col_dict[token_string.strip()] = token_string.strip()

                elif ('.' in token_string) and (token_fmt1[1] == '*'):
                    col_dict[token_fmt1[1].strip()] = token_string.strip()

                elif (token_string == '*') and ('.' not in token_string):
                    col_dict['*'] = '*'

        if type(token) == sqlparse.sql.Identifier:
            if '*' in str(token):
                col_dict['*'] = '*'
            for idl_token in sql_identifier_list:
                if str(token) == idl_token:
                    idl_token_l = idl_token.split('.')
                    col_dict[idl_token_l[1].strip().replace('\t', '').replace('\n', '')] = idl_token.strip().replace('\t', '').replace('\n', '')
    return col_dict


def get_keys(sql):
    '''
    :param sql: valid sql query string
    :return: (table_dictionary, column_dictionary
    '''

    table_dict = dict()
    col_dict = dict()

    sql_statement_lower = str(sql).lower()
    sql_statement_upper = str(sqlparse.format(sql_statement_lower, reindent=True, keyword_case='upper'))
    sql_statement = sql_statement_upper

    parsed_sql = sqlparse.parse(sql_statement)
    sql_statement = parsed_sql[0]

    # Get the column-logic dict for the current sql statement
    col_dict = get_cols(sql_statement)

    for token in sql_statement.tokens:
        if type(token) == sqlparse.sql.Identifier:
            token = str(token).strip().replace('\t', '').replace('\n', '')

            table_map = str(token).split(' ')
            table_map_as = str(token).rsplit(' AS ')

            if 'SELECT' in str(token):
                sql_pattern = re.compile('\((.*)\)', re.DOTALL)
                sql_pattern_str = sql_pattern.findall(str(token))
                sql_pattern1 = re.compile('\(.*\)\s*(.*)$', re.DOTALL)
                sql_pattern_str1 = sql_pattern1.findall(str(token))
                if 'AS ' in sql_pattern_str1[0]:
                    sql_pattern_str1[0] = sql_pattern_str1[0].rsplit(' ', 1)[-1]

                sub_col_dict = dict()
                sub_table_dict = dict()
                sub_table_dict_updated = dict()
                sub_table_dict, sub_col_dict = get_keys(sql_pattern_str[0])

                for table in sub_table_dict.items():
                    if '.' not in table[0]:
                        sub_table_dict_updated[table[0]] = table[1]

                table_dict[sql_pattern_str1[0]] = sub_table_dict_updated
                col_dict[sql_pattern_str1[0]] = sub_col_dict

                # Below logic is used to expand the wildcard statements
                if '*' in col_dict.keys():
                    if '.' in col_dict['*'] and col_dict['*'].split('.')[0] in col_dict.keys():
                        if isinstance(col_dict[col_dict['*'].split('.')[0]], dict):
                            for w_cols in col_dict[col_dict['*'].split('.')[0]].items():
                                if (not isinstance(w_cols[0], dict)) and (not isinstance(col_dict[sql_pattern_str1[0]][w_cols[0]], dict)):
                                    col_dict[w_cols[0]] = col_dict['*'].split('.')[0] + '.' + w_cols[0]
                                elif isinstance(w_cols[1], dict):
                                    for sub_w_cols in w_cols[1].items():
                                        if not isinstance(sub_w_cols[1], dict):
                                            col_dict[sub_w_cols[0]] = sql_pattern_str1[0] + '.' + sub_w_cols[0]
                    elif '.' not in col_dict['*']:
                        if isinstance(col_dict[sql_pattern_str1[0]], dict):
                            for wa_cols in col_dict[sql_pattern_str1[0]].items():
                                if not isinstance(wa_cols[1], dict):
                                    col_dict[wa_cols[0]] = sql_pattern_str1[0] + '.' + wa_cols[0]
                                elif isinstance(wa_cols[1], dict):
                                    for sub_wa_cols in wa_cols[1].items():
                                        if not isinstance(sub_wa_cols[1], dict):
                                            col_dict[sql_pattern_str1[0]][sub_wa_cols[0]] = wa_cols[0] + '.' + sub_wa_cols[0]
                        else:
                            print("No alias for the wildcard")

                if '' in col_dict.keys():
                    del col_dict['']
                if '*' in col_dict.keys():
                    del col_dict['*']

            elif len(table_map_as) > 1:
                table_dict[table_map_as[1].strip()] = table_map_as[0].strip()
            elif len(table_map) > 1:
                table_dict[table_map[1]] = table_map[0]
            else:
                table_dict[table_map[0]] = table_map[0]
    if '' in col_dict.keys():
        del col_dict['']
    if '*' in col_dict.keys():
        del col_dict['*']

    table_dict_updated = dict()
    for t in table_dict.items():
        if '.' not in t[0]:
            table_dict_updated[t[0]] = t[1]
    return table_dict_updated, col_dict


def get_without_alias(col_val, alias_d, col_val_dict):
    '''
    :param col_val: column which doesnt has alias
    :param alias_d: table dictionary
    :param col_val_dict: column dictionary
    :return: column mapping string
    '''
    ret_val = col_val
    col_nam_pat3 = re.compile('[a-zA-Z_0-9]+\.[a-zA-Z_0-9]+')
    repl_cols3 = list(set(col_nam_pat3.findall(col_val)))
    repl_cols3 = [new_repl for new_repl in repl_cols3 if new_repl not in ['ss.SSS', 'ss.sss']]

    if '.' not in col_val:
        for i in alias_d.items():

            if isinstance(i[1], dict):
                try:
                    if col_val in col_val_dict[i[0]].keys():
                        ret_val = str(col_val_dict[i[0]][col_val])
                        if ('.' in ret_val) and (ret_val.split('.')[0] in alias_d[i[0]].keys()) and (
                                not isinstance(alias_d[i[0]][ret_val.split('.')[0]], dict)):
                            ret_val = str(alias_d[i[0]][ret_val.split('.')[0]]) + '.' + str(ret_val.split('.')[1])
                            break
                        else:
                            col_val = get_without_alias(ret_val, alias_d[i[0]], col_val_dict[i[0]])
                            ret_val = col_val
                except:
                    continue
            else:
                ret_val = str(col_val)
    else:
        for repl_len in repl_cols3:
            repl_pat = re.compile('\\b' + repl_len)
            test_out = get_subcol(alias_d, col_val_dict, ret_val, repl_len, ret_val, ret_val)
            ret_val = repl_pat.sub(test_out, ret_val)
    return ret_val


def get_subcol(table_map, column_map, main_str_col, cur_str_col, view_col, real_col_value):
    '''
    :param table_map:
    :param column_map:
    :param main_str_col:
    :param cur_str_col:
    :param view_col:
    :param real_col_value:
    :return:
    '''
    col_nam_pat2 = re.compile('[a-zA-Z_0-9]+\.[a-zA-Z_0-9]+')

    colls_list = list(set(col_nam_pat2.findall(cur_str_col)))
    colls_list_copy = copy.deepcopy(colls_list)

    for colls in colls_list:
        repl_cols2l = colls.split('.')
        for alias in table_map.items():
            alias_pat = re.findall("\\b" + alias[0] + "\.\\b", colls)
            if len(alias_pat) > 0 and (alias_pat[0] in colls):
                if not isinstance(alias[1], dict):
                    new_pat = re.compile('\\b' + alias[0] + '\.', re.I)
                    column_map[view_col] = new_pat.sub(alias[1] + '.', cur_str_col)

                    if len(colls_list_copy) == 1:
                        if column_map[view_col] is not None:
                            return column_map[view_col]
                        else:
                            return cur_str_col
                    else:
                        cur_str_col = column_map[view_col]
                        colls_list_copy.pop(0)
                        break
                elif isinstance(alias[1], dict):
                    try:
                        test_pat = re.compile(colls)
                        sub_value = test_pat.sub("( " + column_map[repl_cols2l[0]][repl_cols2l[1]] + " )", real_col_value)
                        return get_subcol(table_map[alias[0]], column_map[alias[0]], main_str_col, column_map[repl_cols2l[0]][repl_cols2l[1]], view_col, sub_value)
                    except:
                        print("There is some problem with this column.....")
                        return real_col_value

        else:
            return cur_str_col

    if '.' not in cur_str_col:
        print("This column doesn't have ALIAS...")
        return get_without_alias(cur_str_col, table_map, column_map)


def get_metadata(inp):
    '''
    :param inp: file or string
    :return: (table_dictionary, column_dictionary)
    '''
    if os.path.isfile(inp):
        sql_str = open(inp, 'r+').read()
    else:
        sql_str = inp

    table_dict, col_dict = get_keys(sql_str)

    col_dict_copy = copy.deepcopy(col_dict)

    if len(col_dict_copy.keys()) == 1 and isinstance(col_dict_copy[list(col_dict_copy.keys())[0]], dict):
        col_dict_copy = col_dict_copy[col_dict_copy.keys()[0]]
        table_dict = table_dict[table_dict.keys()[0]]

    col_dict_out = dict()
    for cols in col_dict_copy.items():
        if not isinstance(cols[1], dict):
            for als in table_dict.items():
                als_pat = re.findall("\\b" + als[0] + "\.\\b", cols[1])
                if len(als_pat) > 0 and (als_pat[0] in cols[1]):
                    if not isinstance(als[1], dict):
                        new_pat = re.compile('\\b' + als[0] + '\.', re.I)
                        col_dict_out[cols[0]] = new_pat.sub(als[1] + '.', col_dict_copy[cols[0]])
                    elif isinstance(als[1], dict):
                        col_nam_pat1 = re.compile('[a-zA-Z_0-9]+\.[a-zA-Z_0-9]+')
                        repl_cols = list(set(col_nam_pat1.findall(cols[1])))
                        for repl in repl_cols:
                            test_real_column_value = col_dict_copy[cols[0]]
                            if len(repl_cols) == 1:
                                try:
                                    col_dict_out[cols[0]] = col_dict_copy[als[0]][repl.split('.')[1]]
                                    col_dict_out[cols[0]] = get_subcol(table_dict[als[0]], col_dict_copy[als[0]], repl, col_dict_out[cols[0]],
                                                                       cols[0], test_real_column_value)
                                except:
                                    print("There seems to be UNION in Query...")
                                    col_dict_out[cols[0]] = repl

                            elif len(repl_cols) > 1:
                                try:
                                    col_dict_out[repl] = get_subcol(table_dict, col_dict_copy, col_dict_copy[cols[0]], col_dict_copy[cols[0]], cols[0], test_real_column_value)
                                    sub_part_pat = re.compile(repl)
                                    col_dict_out[cols[0]] = sub_part_pat.sub("( " + col_dict_copy[repl] + " )", col_dict_copy[cols[0]])
                                except:
                                    print("Exception...")
                                    col_dict_out[cols[0]] = repl
            if '.' not in cols[1]:
                col_dict_out[cols[0]] = get_without_alias(cols[1], table_dict, col_dict_copy)

    print("**** Database.Table alias mapping ****\n")

    def table_print(t_dict, sep=''):
        for key, value in t_dict.items():
            if isinstance(value, dict):
                print(f"Subquery mapping alias: {key}")
                sep = sep + '\t'
                table_print(value, sep)
            else:
                print(f"{sep}{key} -> {value}")

    table_print(table_dict)

    print("\n\n**** Column, Database and Table mapping ****\n")
    for key, value in col_dict_out.items():
        print(f"{key} -> {value}")

    return table_dict, col_dict_out
