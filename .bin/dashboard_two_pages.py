import os
from junitparser import JUnitXml
from datetime import datetime
from string import Template
from random import randint
import json
from datetime import date

report_file = 'report.xml'
dashboard_file = os.path.join(os.getcwd(), '.html', 'wirecard-test-results-two-pages.html')
test_file = os.path.join(os.getcwd(), '.html', 'wirecard-single-test-result.html')
report_file_link = "https://rawcdn.githack.com/wirecard/reports/master/$project/$gateway/$date/report.html"
fail_test = '<img class="FAIL" src="../.bin/fail.png" height="25" width="25">'
pass_test = '<img class="PASS" src="../.bin/success.png" height="25" width="25">'
date_format = '%Y-%m-%d'
html_header = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Wirecard Gateway Test Results</title><link href="https://file.myfontastic.com/YtqivGkm3YfAnbEZneHr89/icons.css" rel="stylesheet"/><link href="../.bin/simple.css" rel="stylesheet"/><link href="//maxcdn.bootstrapcdn.com/font-awesome/4.1.0/css/font-awesome.min.css" rel="stylesheet"><link href="https://fonts.googleapis.com/css?family=Roboto&display=swap" rel="stylesheet"></head><body><main>'''
html_test_header = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Wirecard Gateway Test Results</title><link href="https://file.myfontastic.com/YtqivGkm3YfAnbEZneHr89/icons.css" rel="stylesheet"/><link href="../.bin/simple.css" rel="stylesheet"/><link href="//maxcdn.bootstrapcdn.com/font-awesome/4.1.0/css/font-awesome.min.css" rel="stylesheet"><link href="https://fonts.googleapis.com/css?family=Roboto&display=swap" rel="stylesheet"></head><body>'''

ignore_folders = [".bin", "docs", ".git", ".idea", ".html"]
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


# 2019-08-26
def get_date_from_report_link_data(project_name, gateway):
    date_dict = filter(lambda gateway_dict: gateway_dict.get(gateway), report_link_data[project_name])
    s_date = date_dict[0][gateway]
    return s_date


# find report.xml file {C:\dev\code\FAKE REPOSITORIES\dashboard-two-pages\woocommerce-ee-3.7.0\API-WDCEE-TEST\2019-08-26\report.xml}
def find_latest_result_file(location, project, gateway):
    global report_link_data
    dates = []
    if os.path.isdir(location):
        for sub_dirs in os.listdir(location):
            dates.append(datetime.strptime(sub_dirs, date_format))
        latest = max(d for d in dates)
        report_link_data = add_to_dict_array(report_link_data, project, {gateway: latest.strftime(date_format)})
        # <------------------------------------------->
        # for dirs in os.listdir(os.path.abspath(os.path.join(location, latest.strftime(date_format)))):
        #     print dirs
        # return os.path.join(location, latest.strftime(date_format), dirs, report_file)
        # <------------------------------------------->
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


# gateway + test name + status {{'API-WDCEE-TEST': {'CreditCard3DSAuthorizeHappyPath: authorize': '<img class="PASS" src="../.bin/success.png" height="25" width="25">'}
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


# gateway + test name + status {{'API-WDCEE-TEST': {'CreditCard3DSAuthorizeHappyPath: authorize': '<img class="PASS" src="../.bin/success.png" height="25" width="25">'}
def reformat_dictionary(dictionary):
    new_dict = {}
    for project, gateway in dictionary.items():
        for gateway_dict in gateway:
            for gateway_name, results in gateway_dict.items():
                new_dict = add_to_dict_array(new_dict, gateway_name, {project: results})
    return new_dict


def create_report_file():
    number = 0
    save = {}
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

                    #last_executed_test_date = get_date_from_report_link_data(project_name, gateway)

                    if duplicate != get_version[0] and duplicate is not None:
                        html_table += '''</div></div></div>'''
                    if duplicate != get_version[0]:
                        html_table += '''<div class="column"><div class="card"><h3>{}</h3><div class="flex-grid-thirds">'''.format(get_version[0].capitalize())
                        duplicate = get_version[0]
                    pop_up += 1
                    array = []

                    for test_name, test_result in sorted(test_results.items()):
                        if save.has_key(project_name):
                            save[project_name].append(test_result)
                        else:
                            save[project_name] = [test_result]
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
                    with open('phpCompatibleVersions.json') as jsonFile:
                        data = json.load(jsonFile)
                    last_executed_test_date = get_date_from_report_link_data(project_name, gateway)
                    last_executed_test = datetime.strptime(last_executed_test_date, '%Y-%m-%d').strftime('%d/%m/%y')
                    today = date.today()
                    current_date = today.strftime("%d/%m/%y")
                    a = datetime.strptime(current_date, "%d/%m/%y")
                    b = datetime.strptime(last_executed_test, "%d/%m/%y")
                    delta = a - b
                    only_days = delta.days
                    if int(only_days) < 1:
                        only_days = "0 day(s) ago"
                    else:
                        only_days = str(delta.days) + "day(s) ago"
                    for i in data:
                        for keys, values in i.items():
                            if get_version[0].capitalize() == keys:
                                html_table_single_test += '''<div id="popup{}" class="overlay"><div class="popup_single"><div class="gateway">{} <span class="date" style="float: right; font-size: 17px !important; font-weight: 100 !important;">Tested: {}</span><span class="description" style="float: right; font-size: 17px !important; font-weight: 100 !important;">{}</span></div><div class="shop-version"><span>{}</span> <span>{}</span></div><div style="padding-top: 5px;"><span style="font-size: 20px; font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;">PHP {}</span></div><div><hr></div><table class="table-report"><tr>'''.format(pop_up, gateway, only_days, last_executed_test, get_version[0].capitalize(), get_version[2], values)
                    for test_name, test_result in sorted(test_results.items()):

                        s_date = get_date_from_report_link_data(project_name, gateway)
                        report_link = Template(report_file_link).substitute({"project": project_name, "gateway": gateway, "date": s_date})

                        for value in [test_name, test_result, '''<td align="right" style="vertical-align: top;"><a class="reports-link" href="{}" target="_blank">SHOW REPORT</a></td></tr><tr>'''.format(report_link)]:
                            html_table += '''<td align="left">{}</td>'''.format(value)
                            html_table_single_test += '''<td align="left">{}</td>'''.format(value)
                    html_table += '''</tr></table></div></div>'''
                    html_table_single_test += '''</tr></table><table class="back-to-overview-table"><tr><td style="margin-top: 10px;"><a class="back-to-overview" href="wirecard-test-results-two-pages.html"><i class="fa fa-long-arrow-left fa-lg"></i>   DASHBOARD</a></td></tr></table></div></div>'''
                else:
                    if duplicate != project_name and duplicate is not None:
                        html_table += '''</div></div></div>'''
                    if duplicate != project_name:
                        html_table += '''<div class="column"><div class="card"><h3>{}</h3><div class="flex-grid-thirds">'''.format(project_name.capitalize())
                        duplicate = project_name
                    pop_up += 1
                    array = []
                    for test_name, test_result in sorted(test_results.items()):
                        if save.has_key(project_name):
                            save[project_name].append(test_result)
                        else:
                            save[project_name] = [test_result]
                        array.append(test_result)

                    result = len(list(set(array)))

                    last_executed_test_date = get_date_from_report_link_data(project_name, gateway)
                    last_executed_test = datetime.strptime(last_executed_test_date, '%Y-%m-%d').strftime('%d/%m/%y')

                    today = date.today()
                    current_date = today.strftime("%d/%m/%y")
                    a = datetime.strptime(current_date, "%d/%m/%y")
                    b = datetime.strptime(last_executed_test, "%d/%m/%y")
                    delta = a - b
                    only_days = delta.days
                    if int(only_days) < 1:
                        only_days = "0 day(s) ago"
                    else:
                        only_days = str(delta.days) + "day(s) ago"

                    if result > 1:
                        html_table += '''<div class="col"><a href="wirecard-single-test-result.html#popup{}">Results</a></div>'''.format(pop_up)
                    else:
                        html_table += '''<div class="col hide" style="background: #9dd53a !important; margin-left: 35%;"><a href="wirecard-single-test-result.html#popup{}">Results</a></div>'''.format(pop_up)
                    html_table += '<div id="popup{}" class="overlay"><div class="popup"><a class="close" href="#">&times;</a><table class="table-report"><tr>'.format(pop_up)
                    html_table_single_test += '''<div id="popup{}" class="overlay"><div class="popup_single"><div class="gateway">{} <span class="date" style="float: right; font-size: 17px !important; font-weight: 100 !important;">Tested: {}</span><span class="description" style="float: right; font-size: 17px !important; font-weight: 100 !important;">{}</span></div><div class="shop-version"><span>{}</span> </div><div><hr></div><table class="table-report"><tr>'''.format(pop_up, gateway, only_days, last_executed_test, project_name.capitalize())
                    for test_name, test_result in sorted(test_results.items()):
                        s_date = get_date_from_report_link_data(project_name, gateway)
                        report_link = Template(report_file_link).substitute({"project": project_name, "gateway": gateway, "date": s_date})
                        for value in [test_name, test_result, '<td align="right" style="vertical-align: top;"><a class="reports-link" href="{}" target="_blank">SHOW REPORT</a></td></tr>'.format(report_link)]:
                            html_table += '<td align="left">{}</td>'.format(value)
                            html_table_single_test += '''<td align="left">{}</td>'''.format(value)
                    html_table += '</tr></table></div></div>'
                    html_table_single_test += '</tr></table><table class="back-to-overview-table"><tr><td style="vertical-align: middle;"><a class="back-to-overview" href="wirecard-test-results-two-pages.html"><i class="fa fa-long-arrow-left fa-lg"></i>   DASHBOARD</a></td></tr></table></div></div>'
        html_table += '''</div></div></div></div></section>'''

    html_table += '''</main>
                       
                            '''
    html_table += '''

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
                    
                    <button onclick="myFunction()" class="button_show_red_only" align="center">SHOW RED ONLY</button>
                    </body></html>'''

    html_table_single_test += '''</body></html>'''

    with open(dashboard_file, 'w') as template_file:
        template_file.write(html_table)
    with open(test_file, 'w') as template_file:
        template_file.write(html_table_single_test)


def main():
    create_report_file()


if __name__ == "__main__":
    main()
