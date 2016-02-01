from datetime import datetime


def list_input(prompt, valid_inputs):
    prompt += ': '
    valid = False
    while not valid:
        user_input = input(prompt)
        valid = user_input in valid_inputs
        if not valid:
            print('invalid input')
    return user_input


def type_input(prompt, data_type, default=None):
    valid = False
    if default is not None:
        prompt += ' ({})'.format(default)
    prompt += ': '
    while not valid:
        user_input = input(prompt)
        if default is not None and user_input == '':
            return default
        try:
            user_input = data_type(user_input)
            valid = True
        except ValueError as e:
            print ("'{}' is not of type {}".format(
                   e.args[0].split(": ")[1],
                   data_type.__name__))
    return user_input


def str_input(prompt, default=None):
    return type_input(prompt, str, default=default)


def dt_input(prompt, time_prompt=None):
    correct_format = False
    while not correct_format:
        date_string = str_input(prompt + ' (YYYY-MM-DD)')
        try:
            ret = datetime.strptime(date_string, '%Y-%m-%d')
            correct_format = True
        except ValueError:
            print('Date input does not have required format.')

    if time_prompt is not None:
        correct_format = False
        while not correct_format:
            time_string = str_input(time_prompt + '(HH:MM)')
            try:
                full_time = date_string + ' ' + time_string
                ret = datetime.strptime(full_time, '%Y-%m-%d %H:%M')
                correct_format = True
            except ValueError:
                print('Time input does not have required format.')

    return ret


def bool_question(question, default=None):
    yes_list = ['y', 'Y', 'j', 'J']
    no_list = ['n', 'N']
    if default is True:
        question += ' (Y/n)'
        yes_list.append('')
    elif default is False:
        question += ' (y/N)'
        no_list.append('')
    else:
        question += ' (y/n)'
    answer = list_input(question, yes_list + no_list)
    return answer in yes_list


def list_choice(list):
    i = 1
    for item in list:
        print('{index} - {item}'.format(index=i, item=item))
        i += 1

    valid_inputs = [str(x) for x in range(1, i)]
    choice = int(list_input('choice from list', valid_inputs))
    return list[choice - 1]


def query_choice(query):
    identifiers = {}
    has_name = hasattr(query.first(), 'name')
    for item in query:
        if has_name:
            identifiers[item.name] = item.id
        else:
            identifiers[str(item)] = item.id

    choosen_name = list_choice(list(identifiers.keys()))
    return query.get(identifiers[choosen_name])
