import json
import re

data_fields = ["bus_id", "stop_id", "stop_name", "next_stop", "stop_type", "a_time"]
database_rules = {
        "bus_id": {'type': int, 'required': True, 'format': None},
        "stop_id": {'type': int, 'required': True, 'format': None},
        "stop_name": {'type': str, 'required': True, 'format': "([A-Z][a-z]+ )+(Road|Avenue|Boulevard|Street)$"},
        "next_stop": {'type': int, 'required': True, 'format': None},
        "stop_type": {'type': str, 'required': False, 'format': '[SOF]$'},
        "a_time": {'type': str, 'required': True, 'format': '(2[0-3]|[0-1][0-9]):([0-5][0-9])$'}
        }


def is_valid_stop_types(counters):
    for counter in counters:
        if len(counter['S']) == 0 or len(counter['F']) == 0:
            print(f'There is no start or end stop for the line: {counter["bus_id"]}.')
            return False
        elif len(counter['S']) > 1 or len(counter['F']) > 1:
            print(f'There is too many start or end stops for the line: {counter["bus_id"]}.')
            return False

    return True


def is_error_field(value, data_rules):
    if not data_rules['required'] and value == '':
        return False

    if value == '':
        return True
    elif type(value) != data_rules['type']:
        return True
    elif data_rules['format'] is not None and re.match(data_rules['format'], value) is None:
        return True

    return False


def find_errors(easy_rider_json, fields):
    errors = {field: 0 for field in fields}

    for data_point in easy_rider_json:
        for field, value in data_point.items():
            if is_error_field(value, database_rules[field]):
                errors[field] += 1

    return errors


def print_pretty(errors):
    summary = sum(errors.values())

    print(f'Type and required field validation: {summary} errors')
    for field, value in errors.items():
        print(f'{field}: {value}')


def print_pretty_2(lines, stations_stops):
    stations_stops = [len(ids) for ids in stations_stops]
    print('Line names and number of stops:')
    for line_number, line in enumerate(lines):
        print(f'bus_id: {line}, stops: {stations_stops[line_number]}')


def print_pretty_3(counters):
    starts = set()
    transfers = set()
    finishes = set()

    for counter in counters:
        starts.update(counter['S'])
        finishes.update(counter['F'])
        for counter2 in counters:
            if counter['bus_id'] != counter2['bus_id']:
                transfers.update(counter['A'].intersection(counter2['A']))

    print(f'Start stops: {len(starts)} {sorted(list(starts))}')
    print(f'Transfer stops: {len(transfers)} {sorted(list(transfers))}')
    print(f'Finish stops: {len(finishes)} {sorted(list(finishes))}')


def print_pretty_4(incorrect_stops):
    print('Arrival time test:')
    flag = True

    for line, incorrect_stop in incorrect_stops.items():
        if incorrect_stop is not None:
            print(f'bus_id line {line}: wrong time on station {incorrect_stop}')
            flag = False

    if flag:
        print('OK')


def find_lines(data, data_rules):
    lines = set()

    for data_point in data:
        if not is_error_field(data_point['bus_id'], data_rules['bus_id']):
            lines.add(data_point['bus_id'])

    return lines


def find_lines_info(data, lines, field):
    stop_names = [list() for _ in lines]
    for data_point in data:
        for line_num, line in enumerate(lines):
            stop_names[line_num].append(data_point[field])

    return stop_names


def verify_stops(data, data_rules):
    lines = list(find_lines(data, data_rules))
    stations_stops = find_lines_info(data, lines)
    print_pretty_2(lines, stations_stops)


def verify_stop_types(data, data_rules, need_return=False):
    lines = list(find_lines(data, data_rules))
    stop_types_counter = [{'bus_id': line, 'S': list(), 'A': set(), 'F': list()} for line in lines]

    for counter in stop_types_counter:
        for data_point in data:
            if data_point['bus_id'] == counter['bus_id']:
                if data_point['stop_type'] == 'S' or data_point['stop_type'] == 'F':
                    counter[data_point['stop_type']].append(data_point['stop_name'])
                counter['A'].update([data_point['stop_name']])

    if need_return:
        return stop_types_counter
    if is_valid_stop_types(stop_types_counter):
        print_pretty_3(stop_types_counter)


def verify_stop_times(data, data_rules):
    lines = list(find_lines(data, data_rules))
    incorrect_stops = {line: None for line in lines}

    for line in lines:
        time = None
        for data_point in data:
            if data_point['bus_id'] == line:
                if time is None:
                    time = data_point['a_time']
                elif data_point['a_time'] > time:
                    time = data_point['a_time']
                else:
                    incorrect_stops[line] = data_point['stop_name']
                    break
    print_pretty_4(incorrect_stops)


def get_key_stations(counters):
    starts = set()
    transfers = set()
    finishes = set()

    for counter in counters:
        starts.update(counter['S'])
        finishes.update(counter['F'])
        for counter2 in counters:
            if counter['bus_id'] != counter2['bus_id']:
                transfers.update(counter['A'].intersection(counter2['A']))
    result = set()
    result.update(starts)
    result.update(finishes)
    result.update(transfers)
    return result


def verify_on_demand_stops(data, data_rules):
    print('On demand stops test:')
    lines = list(find_lines(data, data_rules))
    key_stops = get_key_stations(verify_stop_types(data, data_rules, True))
    errors = set()

    for data_point in data:
        for line in lines:
            if data_point['bus_id'] == line:
                if data_point['stop_type'] == 'O' and data_point['stop_name'] in key_stops:
                    errors.update([data_point['stop_name']])

    errors = sorted(list(errors))
    if errors:
        print(f'Wrong stop type: {errors}')
        return

    print('OK')


def main():
    easy_rider_json = json.loads(input())
    verify_on_demand_stops(easy_rider_json, database_rules)


if __name__ == '__main__':
    main()
