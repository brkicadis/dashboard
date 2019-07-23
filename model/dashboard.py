import os
from junitparser import JUnitXml
from datetime import datetime
from string import Template
from random import randint

report_file = 'report.xml'
dashboard_file = os.path.join(os.getcwd(), 'output', 'wirecard-test-results-two-pages.html')
test_file = os.path.join(os.getcwd(), 'output', 'wirecard-single-test-result.html')
report_file_link = "https://rawcdn.githack.com/wirecard/reports/master/$project/$gateway/$date/report.html"
fail_test = '<span style="color:red">FAIL</span>'
pass_test = '<span style="color:green">PASS</span>'
date_format = '%Y-%m-%d'
html_header = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Wirecard Gateway Test Results</title><link href="https://file.myfontastic.com/YtqivGkm3YfAnbEZneHr89/icons.css" rel="stylesheet"/><link href="../css/simple.css" rel="stylesheet"/><link href="//maxcdn.bootstrapcdn.com/font-awesome/4.1.0/css/font-awesome.min.css" rel="stylesheet"></head><body><main>'''
html_test_header = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Wirecard Gateway Test Results</title><link href="https://file.myfontastic.com/YtqivGkm3YfAnbEZneHr89/icons.css" rel="stylesheet"/><link href="../css/simple.css" rel="stylesheet"/><link href="//maxcdn.bootstrapcdn.com/font-awesome/4.1.0/css/font-awesome.min.css" rel="stylesheet"></head><body>'''

ignore_folders = ["css", "model", ".git", ".idea", "output"]
report_link_data = {}


def add_to_dict_array(input_dict, key,  value):
    try:
        array_results = input_dict[key]
        if value not in array_results:
            array_results.append(value)
            input_dict[key] = array_results
    except KeyError:
        array_results = []
        if value not in array_results:
            array_results.append(value)
            input_dict[key] = array_results
    return input_dict


def get_date_from_report_link_data(project_name, gateway):
    date_dict = filter(lambda gateway_dict: gateway_dict.get(gateway), report_link_data[project_name])
    date = date_dict[0][gateway]
    return date


def find_latest_result_file(location, project, gateway):
    global report_link_data
    dates = []
    if os.path.isdir(location):
        for sub_dirs in os.listdir(location):
            dates.append(datetime.strptime(sub_dirs, date_format))
        latest = max(d for d in dates)
        report_link_data = add_to_dict_array(report_link_data, project, {gateway: latest.strftime(date_format)})
        return os.path.join(location, latest.strftime(date_format), report_file)
    else:
        return None


def process_results_file(gateway, result_file):
    gateway_res = {}
    features = {}
    xml = JUnitXml.fromfile(result_file)
    for suite in xml:
        for case in suite:
            feature_name = case.name
            if feature_name not in features.keys():
                features[feature_name] = pass_test
            if case.result:
                features[feature_name] = fail_test
    gateway_res[gateway] = features
    return gateway_res


def process_results_files():
    test_results = {}
    root_dir = os.getcwd()
    for dir in os.listdir(root_dir):
        if dir not in ignore_folders and os.path.isdir(dir):
            project = dir
            gateway_results = []
            for sub_dirs in os.listdir(os.path.join(root_dir, dir)):
                gateway = sub_dirs
                result_file = find_latest_result_file(os.path.join(root_dir, dir, sub_dirs), project, gateway)
                if result_file:
                    gateway_results.append(process_results_file(gateway, result_file))
            test_results[project] = gateway_results
    return reformat_dictionary(test_results)


def reformat_dictionary(dictionary):
    new_dict = {}
    for project, gateway in dictionary.items():
        for gateway_dict in gateway:
            for gateway_name, results in gateway_dict.items():
                new_dict = add_to_dict_array(new_dict, gateway_name, {project: results})
    return new_dict


def create_report_file():
    number = 0
    results = process_results_files()
    html_table = html_header
    html_table_single_test = html_test_header
    for gateway, project_results in sorted(results.items()):
        number += 1
        if 'API-TEST' == gateway:
            html_table += '''<input id="tab{}" type="radio" name="tabs" checked><label for="tab{}">{}</label>'''.format(number, number, gateway)
        else:
            html_table += '''<input id="tab{}" type="radio" name="tabs"><label for="tab{}">{}</label>'''.format(number, number, gateway)
    number = 0
    for gateway, project_results in sorted(results.items()):
        duplicate = None
        number += 1
        html_table += '''<section id="content{}"><div class="row">'''.format(number)
        pop_up = randint(0, 5000)
        for project in sorted(project_results):
            for project_name, test_results in sorted(project.items()):
                if project_name != 'paymentSDK-php':
                    get_version = project_name.split('-')
                    if duplicate != get_version[0] and duplicate is not None:
                        html_table += '''</div></div></div>'''
                    if duplicate != get_version[0]:
                        html_table += '''<div class="column"><div class="card"><h3>{}</h3><div class="flex-grid-thirds">'''.format(get_version[0].capitalize())
                        duplicate = get_version[0]
                    pop_up += 1

                    array = []
                    for test_name, test_result in sorted(test_results.items()):
                        array.append(test_result)
                    res = list(set(array))
                    result = len(list(set(array)))

                    if result < 2 and fail_test in res:
                        html_table += '''<div class="col"><a href="wirecard-single-test-result.html#popup{}">{}</a></div>'''.format(pop_up, get_version[2])

                    elif result > 1:
                        html_table += '''<div class="col"><a href="wirecard-single-test-result.html#popup{}">{}</a></div>'''.format(pop_up, get_version[2])
                    else:
                        html_table += '''<div class="col hide" style="background: #9dd53a !important;"><a href="wirecard-single-test-result.html#popup{}">{}</a></div>'''.format(pop_up, get_version[2])
                    html_table += '''<div id="popup{}" class="overlay"><div class="popup"><a class="close" href="#">&times;</a><table class="table-report"><tr>'''.format(pop_up)
                    html_table_single_test += '''<div id="popup{}" class="overlay"><div class="popup_single"><div class="gateway">{}</div><div class="shop-version"><span>{}</span> <span>{}</span></div><div><hr></div><table class="table-report"><tr>'''.format(pop_up, gateway, get_version[0].capitalize(), get_version[2])
                    for test_name, test_result in sorted(test_results.items()):
                        date = get_date_from_report_link_data(project_name, gateway)
                        report_link = Template(report_file_link).substitute({"project": project_name, "gateway": gateway, "date": date})

                        for value in [test_name, test_result, '''<td align="right"><a class="reports-link" href="{}">REPORT</a></td></tr><tr>'''.format(report_link)]:
                            html_table += '''<td align="left">{}</td>'''.format(value)
                            html_table_single_test += '''<td align="left">{}</td>'''.format(value)
                    html_table += '''</tr></table></div></div>'''
                    html_table_single_test += '''</tr></table><table class="back-to-overview-table"><tr><td><a class="back-to-overview" href="wirecard-test-results-two-pages.html"><i class="fa fa-chevron-left"></i>   BACK TO OVERVIEW</a></td></tr></table></div></div>'''
                else:
                    if duplicate != project_name and duplicate is not None:
                        html_table += '''</div></div></div>'''
                    if duplicate != project_name:
                        html_table += '''<div class="column"><div class="card"><h3>{}</h3><div class="flex-grid-thirds">'''.format(project_name.capitalize())
                        duplicate = project_name
                    pop_up += 1
                    array = []
                    for test_name, test_result in sorted(test_results.items()):
                        array.append(test_result)
                    result = len(list(set(array)))

                    if result > 1:
                        html_table += '''<div class="col"><a href="wirecard-single-test-result.html#popup{}">Results</a></div>'''.format(pop_up)
                    else:
                        html_table += '''<div class="col hide" style="background: #9dd53a !important;"><a href="wirecard-single-test-result.html#popup{}">Results</a></div>'''.format(pop_up)
                    html_table += '<div id="popup{}" class="overlay"><div class="popup"><a class="close" href="#">&times;</a><table class="table-report"><tr>'.format(pop_up)
                    html_table_single_test += '''<div id="popup{}" class="overlay"><div class="popup_single"><div class="gateway">{}</div><div class="shop-version"><span>{}</span></div><div><hr></div><table class="table-report"><tr>'''.format(pop_up, gateway, project_name.capitalize())
                    for test_name, test_result in sorted(test_results.items()):
                        date = get_date_from_report_link_data(project_name, gateway)
                        report_link = Template(report_file_link).substitute({"project": project_name, "gateway": gateway, "date": date})
                        for value in [test_name, test_result, '<td align="right"><a class="reports-link" href="{}">REPORT</a></td></tr>'.format(report_link)]:
                            html_table += '<td align="left">{}</td>'.format(value)
                            html_table_single_test += '''<td align="left">{}</td>'''.format(value)
                    html_table += '</tr></table></div></div>'
                    html_table_single_test += '</tr></table><table class="back-to-overview-table"><tr><td><a class="back-to-overview" href="wirecard-test-results-two-pages.html"><i class="fa fa-chevron-left"></i>   BACK TO OVERVIEW</a></td></tr></table></div></div>'
        html_table += '''</div></div></div></div></section>'''
    html_table += '''</main>
                        <script>
                            function myFunction() {
                                let x = document.getElementsByClassName("hide");
                                let i;
                                    for (i = 0; i < x.length; i++) {
                                        if (x[i].style.visibility === "hidden") {
                                            x[i].style.visibility = "visible";
                                        } else {
                                            x[i].style.visibility = "hidden";
                                    }
                                }
                            }
                    </script>
                    <button onclick="myFunction()"><span>SHOW RED ONLY</span></button></body></html>'''

    html_table_single_test += '''</body></html>'''

    with open(dashboard_file, 'w') as template_file:
        template_file.write(html_table)
    with open(test_file, 'w') as template_file:
        template_file.write(html_table_single_test)


def main():
    create_report_file()


if __name__ == "__main__":
    main()