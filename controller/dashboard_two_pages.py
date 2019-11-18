import os
from junitparser import JUnitXml
from datetime import datetime
from string import Template
from random import randint
import json
from datetime import date


reportFile = 'report.xml'
dashboardHtmlFile = os.path.join(os.getcwd(), 'view', 'wirecard-test-results-two-pages.html')
dashboardSingleHtmlTestFile = os.path.join(os.getcwd(), 'view', 'wirecard-single-test-result.html')
reportFileLink = "https://rawcdn.githack.com/wirecard/reports/master/$project/$gateway/$date/$branch/report.html"
failTest = '<img class="FAIL" src="../images/fail.png" height="25" width="25">'
passTest = '<img class="PASS" src="../images/success.png" height="25" width="25">'
dateFormat = '%Y-%m-%d'
htmlDashboardTestHeader = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Wirecard Gateway Test Results</title><link href="https://file.myfontastic.com/YtqivGkm3YfAnbEZneHr89/icons.css" rel="stylesheet"/><link href="../css/style.css" rel="stylesheet"/><link href="//maxcdn.bootstrapcdn.com/font-awesome/4.1.0/css/font-awesome.min.css" rel="stylesheet"><link href="https://fonts.googleapis.com/css?family=Roboto&display=swap" rel="stylesheet"></head><body><main id="main"><div id="team">Shop System Test Dashboard</div>'''
htmlDashboardSingleTestHeader = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Wirecard Gateway Test Results</title><link href="https://file.myfontastic.com/YtqivGkm3YfAnbEZneHr89/icons.css" rel="stylesheet"/><link href="../css/style.css" rel="stylesheet"/><link href="//maxcdn.bootstrapcdn.com/font-awesome/4.1.0/css/font-awesome.min.css" rel="stylesheet"><link href="https://fonts.googleapis.com/css?family=Roboto&display=swap" rel="stylesheet"></head><body>'''

searchIgnoreFolders = ["controller", "docs", ".git", ".idea", "view", "venv", "css", "images"]
reportLinkData = {}
githubLinks = {"Magento2": "https://github.com/wirecard/magento2-ee", "Magento": "https://github.com/wirecard/magento-ee", "Shopware": "https://github.com/wirecard/shopware-ee", "Opencart": "https://github.com/wirecard/opencart-ee", "Prestashop": "https://github.com/wirecard/prestashop-ee", "Paymentsdk-php": "https://github.com/wirecard/paymentSDK-php", "Woocommerce": "https://github.com/wirecard/woocommerce-ee"}


def findLatestResultFiles(location):
    global reportLinkData
    if os.path.isdir(location):
        return os.path.join(location, reportFile)
    else:
        return None


def process_results_file(gateway, xmlPathResultFile):
    gatewayTestResults = {}
    testResultsBasedOnGateway = {}
    xml = JUnitXml.fromfile(xmlPathResultFile)
    for testSuite in xml:
        for testCase in testSuite:
            testName = testCase.name
            if testName not in testResultsBasedOnGateway.keys():
                testResultsBasedOnGateway[testName] = passTest
            if testCase.result:
                testResultsBasedOnGateway[testName] = failTest
    gatewayTestResults[gateway] = testResultsBasedOnGateway
    return gatewayTestResults


def findBranches(location):
    listOfFoundedBranches = []
    for branches in os.listdir(location):
        listOfFoundedBranches.append(branches)
    return listOfFoundedBranches


def createTestResultsDictionary():
    searchRootDirectory = os.getcwd() + "/model"
    testResultsDictionary = {}
    for directory in os.listdir(searchRootDirectory):
        if directory not in searchIgnoreFolders:
            pluginName = directory
            gatewayTestResults = []
            for subdirectory in os.listdir(os.path.join(searchRootDirectory, directory)):
                dateDirectory = []
                gateway = subdirectory
                for dates in os.listdir(os.path.join(searchRootDirectory, directory, subdirectory)):
                    dateDirectory.append(datetime.strptime(dates, dateFormat))
                latestDate = max(singleDate for singleDate in dateDirectory)
                convertDateFormat = latestDate.strftime(dateFormat)
                latestDatePath = os.path.join(searchRootDirectory, directory, subdirectory, convertDateFormat)
                findBranches(latestDatePath)
                for branch in findBranches(latestDatePath):
                    reportResultFile = findLatestResultFiles(os.path.join(latestDatePath, branch))
                    if reportResultFile:
                        gatewayTestResults.append(process_results_file(gateway, reportResultFile))
                        # refactorTestResults(gateway, reportResultFile, pluginName, convertDateFormat, branch)
                        for testGateway, testResults in process_results_file(gateway, reportResultFile).iteritems():
                            gatewayBasedTestResults = {testGateway: {pluginName: {convertDateFormat: {branch: testResults}}}}
                            for singleTestGateway, singleGatewayTestResults in gatewayBasedTestResults.iteritems():
                                for testPluginName, pluginNameTestResults in singleGatewayTestResults.iteritems():
                                    for pluginNameBasedDate, dateTestResults in pluginNameTestResults.iteritems():
                                        for dateBasedBranch, branchTestResults in dateTestResults.iteritems():
                                            testResultsDictionary.setdefault(singleTestGateway, {}).setdefault(testPluginName, {}).setdefault(pluginNameBasedDate, {}).update({dateBasedBranch: branchTestResults})
    return testResultsDictionary


def createHtmlTestResultReport():
    tabIncrement = 0
    findProjectKey = {}
    results = createTestResultsDictionary()
    htmlTestResults = htmlDashboardTestHeader
    singleHtmlTestResult = htmlDashboardSingleTestHeader
    for gateway, projectTestResults in sorted(results.items()):
        tabIncrement += 1
        if 'API-TEST' == gateway:
            htmlTestResults += '''<input id="tab{}" type="radio" name="tabs" checked><label for="tab{}">{}</label>'''.format(tabIncrement, tabIncrement, gateway)
        else:
            htmlTestResults += '''<input id="tab{}" type="radio" name="tabs"><label for="tab{}">{}</label>'''.format(tabIncrement, tabIncrement, gateway)

    numberOfPluginTests, numberOfPaymentSdkTests, contentIncrement, numberOfSuccessfulPluginTests, numberOfFailedPluginTests, numberOfSuccessfulPaymentSdkTests, numberOfFailedPaymentSdkTests = (0,)*7

    for gateway, projectTestResults in sorted(results.items()):
        duplicate = None
        contentIncrement += 1
        htmlTestResults += '''<section id="content{}"><div class="row">'''.format(contentIncrement)
        popUpIncrement = randint(0, 5000)

        for projectName, searchProjectTestResults in sorted(projectTestResults.items(), reverse=True):
            if projectName != 'paymentSDK-php':
                global executionDate
                branches = []
                for executionDate, testResults in sorted(searchProjectTestResults.items()):
                    for branch, restTestResults in sorted(testResults.items()):
                        branches.append(branch)

                pluginDetails = projectName.split('-')

                if duplicate != pluginDetails[0] and duplicate is not None:

                    htmlTestResults += '''</div></div></div>'''
                if duplicate != pluginDetails[0]:
                    for githubPluginName, githubPluginLinkPath in githubLinks.items():
                        if githubPluginName == pluginDetails[0].capitalize():
                            htmlTestResults += '''<div class="column"><div class="card"><h3><a class="shop-plugin" target="_blank" href="{}">{}</a></h3>'''.format(githubPluginLinkPath, pluginDetails[0].capitalize())
                    htmlTestResults += '''<div style="width: 100%;"><table style="margin: -70px -20px 30px 0; z-index: 10000; float: right; position: relative;"><tr>'''
                    for branch in branches:
                        htmlTestResults += '''<td><p class="branch">{}</p></td>'''.format(branch)

                    htmlTestResults += '''</tr></table></div><div class="flex-grid-thirds">'''
                    duplicate = pluginDetails[0]

                popUpIncrement += 1
                array = []

                branchesArray = []
                for executionDate, testResults in sorted(searchProjectTestResults.items()):
                    for branch, restTestResults in sorted(testResults.items()):
                        branchesArray.append(branch)
                        for testName, testStatus in sorted(restTestResults.items()):
                            if findProjectKey.has_key(projectName):
                                findProjectKey[projectName].append(testStatus)
                            else:
                                findProjectKey[projectName] = [testStatus]
                            array.append(testStatus)

                if failTest in array:
                    numberOfFailedPluginTests += len(array)
                else:
                    numberOfSuccessfulPluginTests += len(array)
                numberOfPluginTests += len(array)

                res = list(set(array))
                result = len(list(set(array)))
                checkForRelease = len(list(set(branchesArray)))

                if result < 2 and failTest in res:
                    if checkForRelease > 1:
                        htmlTestResults += '''<div class="col"><a class="release-version" href="wirecard-single-test-result.html#popup{}">{}</a><span class="star"> *</span><span class="notification">Release candidate test.</span></div>'''.format(popUpIncrement, pluginDetails[2])
                    else:
                        htmlTestResults += '''<div class="col hide"><a href="wirecard-single-test-result.html#popup{}">{}</a></div>'''.format(popUpIncrement, pluginDetails[2])
                elif result > 1:
                    if checkForRelease > 1:
                        htmlTestResults += '''<div class="col"><a class="release-version" href="wirecard-single-test-result.html#popup{}">{}</a><span class="star"> *</span><span class="notification">Release candidate test.</span></div>'''.format(popUpIncrement, pluginDetails[2])
                    else:
                        htmlTestResults += '''<div class="col"><a href="wirecard-single-test-result.html#popup{}">{}</a></div>'''.format(popUpIncrement, pluginDetails[2])
                else:
                    if checkForRelease > 1:
                        htmlTestResults += '''<div class="col hide" style="background-image: linear-gradient(-180deg,#5cb85c,#4cae4c 80%);"><a class="release-version" href="wirecard-single-test-result.html#popup{}">{}</a><span class="star"> *</span><span class="notification">Release candidate test.</span></div>'''.format(popUpIncrement, pluginDetails[2])
                    else:
                        htmlTestResults += '''<div class="col hide" style="background-image: linear-gradient(-180deg,#5cb85c,#4cae4c 80%);"><a href="wirecard-single-test-result.html#popup{}">{}</a></div>'''.format(popUpIncrement, pluginDetails[2])
                htmlTestResults += '''<div id="popup{}" class="overlay"><div class="popup"><a class="close" href="#">&times;</a><table class="table-report"><tr>'''.format(popUpIncrement)
                with open('controller/phpCompatibleVersions.json') as jsonFile:
                    data = json.load(jsonFile)
                convertDate = datetime.strptime(executionDate, '%Y-%m-%d').strftime('%d/%m/%y')

                today = date.today()
                currentFormatedDate = today.strftime("%d/%m/%y")
                a = datetime.strptime(currentFormatedDate, "%d/%m/%y")
                b = datetime.strptime(convertDate, "%d/%m/%y")
                delta = a - b
                onlyDays = delta.days
                if int(onlyDays) < 1:
                    onlyDays = "0 day(s) ago"
                else:
                    onlyDays = str(delta.days) + " day(s) ago"

                for i in data:
                    for keys, values in i.items():
                        if pluginDetails[0].capitalize() == keys:
                            singleHtmlTestResult += '''<div id="popup{}" class="overlay"><div class="popup_single"><div class="gateway">{} <span class="date" style="float: right; font-size: 17px !important; font-weight: 100 !important;">Tested: {}</span><span class="description" style="float: right; font-size: 17px !important; font-weight: 100 !important;">{}</span></div><div class="shop-version"><span>{}</span> <span>{}</span></div><div style="padding-top: 5px;"><span style="font-size: 20px; font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;">PHP {} </span></div><div><hr></div><table class="table-report">'''.format(popUpIncrement, gateway, onlyDays, executionDate, pluginDetails[0].capitalize(), pluginDetails[2], values)
                for executionDate, testResults in sorted(searchProjectTestResults.items()):
                    for branch, restTestResults in sorted(testResults.items()):
                        singleHtmlTestResult += '''<tr><td><p class="branch-single-test">{}</p></td></tr>'''.format(branch)
                        singleHtmlTestResult += '''<tr>'''
                        for testName, testStatus in sorted(restTestResults.items()):
                            report_link = Template(reportFileLink).substitute({"project": projectName, "gateway": gateway, "date": executionDate, "branch": branch})
                            # print report_link
                            for value in [testName, testStatus, '''<td align="right" style="vertical-align: top;"><p class="branch" href="#" target="_blank">{}</p></td><td align="right" style="vertical-align: top;"><a class="reports-link" href="{}" target="_blank">SHOW REPORT</a></td></tr><tr>'''.format(branch, report_link)]:
                                htmlTestResults += '''<td align="left">{}</td>'''.format(value)

                                singleHtmlTestResult += '''<td align="left">{}</td>'''.format(value)
                htmlTestResults += '''</tr></table></div></div>'''
                singleHtmlTestResult += '''</tr></table><table class="back-to-overview-table"><tr><td style="margin-top: 10px;"><a class="back-to-overview" href="wirecard-test-results-two-pages.html"><i class="fa fa-long-arrow-left fa-lg"></i>   DASHBOARD</a></td></tr></table></div></div>'''
            else:
                branches = []
                for executionDate, testResults in sorted(searchProjectTestResults.items()):
                    for branch, restTestResults in sorted(testResults.items()):
                        branches.append(branch)
                if duplicate != projectName and duplicate is not None:
                    htmlTestResults += '''</div></div></div>'''
                if duplicate != projectName:
                    for key, value in githubLinks.items():
                        if key == projectName.capitalize():
                            htmlTestResults += '''<div class="column"><div class="card"><h3><a class="shop-plugin" href="{}" target="_blank">{}</a></h3>'''.format(value, projectName.capitalize())

                    htmlTestResults += '''<div style="width: 100%;">
                                        <table style="margin: -70px -20px 30px 0; z-index: 10000; float: right; position: relative;"><tr>'''
                    for branch in branches:
                        htmlTestResults += '''<td><p class="branch">{}</p></td>'''.format(branch)

                    htmlTestResults += '''</tr></table>
                                    </div>'''

                    htmlTestResults += '''<div class="flex-grid-thirds">'''
                    duplicate = projectName
                popUpIncrement += 1
                array = []

                for executionDate, testResults in sorted(searchProjectTestResults.items()):
                    for branch, restTestResults in sorted(testResults.items()):
                        for testName, testStatus in sorted(restTestResults.items()):
                            if findProjectKey.has_key(projectName):
                                findProjectKey[projectName].append(testStatus)
                            else:
                                findProjectKey[projectName] = [testStatus]
                            array.append(testStatus)
                result = len(list(set(array)))

                numberOfPaymentSdkTests += len(array)
                if failTest in array:
                    numberOfFailedPaymentSdkTests += len(array)
                else:
                    numberOfSuccessfulPaymentSdkTests += len(array)

                convertDate = datetime.strptime(executionDate, '%Y-%m-%d').strftime('%d/%m/%y')
                today = date.today()
                currentFormatedDate = today.strftime("%d/%m/%y")
                a = datetime.strptime(currentFormatedDate, "%d/%m/%y")
                b = datetime.strptime(convertDate, "%d/%m/%y")
                delta = a - b
                onlyDays = delta.days
                if int(onlyDays) < 1:
                    onlyDays = "0 day(s) ago"
                else:
                    onlyDays = str(delta.days) + " day(s) ago"

                if result > 1:
                    htmlTestResults += '''<div class="col"><a href="wirecard-single-test-result.html#popup{}">Results</a></div>'''.format(popUpIncrement)
                else:
                    htmlTestResults += '''<div class="col hide" style="background-image: linear-gradient(-180deg,#5cb85c,#4cae4c 80%);"><a href="wirecard-single-test-result.html#popup{}">Results</a></div>'''.format(popUpIncrement)
                htmlTestResults += '<div id="popup{}" class="overlay"><div class="popup"><a class="close" href="#">&times;</a><table class="table-report"><tr>'.format(popUpIncrement)
                singleHtmlTestResult += '''<div id="popup{}" class="overlay"><div class="popup_single"><div class="gateway">{} <span class="date" style="float: right; font-size: 17px !important; font-weight: 100 !important;">Tested: {}</span><span class="description" style="float: right; font-size: 17px !important; font-weight: 100 !important;">{}</span></div><div class="shop-version"><span>{} </span> </div><div><hr></div><table class="table-report">'''.format(popUpIncrement, gateway, onlyDays, executionDate, projectName.capitalize())

                for executionDate, testResults in sorted(searchProjectTestResults.items()):
                    for branch, restTestResults in sorted(testResults.items()):
                        singleHtmlTestResult += '''<tr><td><p class="branch-single-test">{}</p></td></tr>'''.format(branch)
                        singleHtmlTestResult += '''<tr>'''
                        for testName, testStatus in sorted(restTestResults.items()):
                            report_link = Template(reportFileLink).substitute({"project": projectName, "gateway": gateway, "date": executionDate, "branch": branch})
                            for value in [testName, testStatus, '''<td align="right" style="vertical-align: top;"><p class="branch" href="#" target="_blank">{}</p></td><td align="right" style="vertical-align: top;"><a class="reports-link" href="{}" target="_blank">SHOW REPORT</a></td></tr><tr>'''.format(branch, report_link)]:
                                htmlTestResults += '''<td align="left">{}</td>'''.format(value)

                                singleHtmlTestResult += '''<td align="left">{}</td>'''.format(value)
                htmlTestResults += '</tr></table></div></div>'
                singleHtmlTestResult += '</tr></table><table class="back-to-overview-table"><tr><td style="vertical-align: middle;"><a id="dashboard" class="back-to-overview" href="wirecard-test-results-two-pages.html"><i class="fa fa-long-arrow-left fa-lg"></i>   DASHBOARD</a></td></tr></table></div></div>'
        htmlTestResults += '''</div></div></div></div></section>'''

    # print numberOfPluginTests, numberOfPaymentSdkTests, numberOfSuccessfulPluginTests, numberOfFailedPluginTests, numberOfFailedPaymentSdkTests, numberOfSuccessfulPaymentSdkTests

    htmlTestResults += '''</main><div class="rotate"></div>'''
    # htmlTestResults += '''<div id="stats"><div class="statistics"><i class="fa fa-bar-chart fa-2x" aria-hidden="true"></i><m style="margin-left: 15px; padding-bottom: 8px; color: black;">{}</m></div><div class="success"><i class="fa fa-check fa-2x" aria-hidden="true"></i></div><div class="fail"><i class="fa fa-times fa-2x" aria-hidden="true"></i></div></div>'''.format(numberOfPluginTests+numberOfPaymentSdkTests)
    htmlTestResults += '''<script>function myFunction() { let x = document.getElementsByClassName("hide"); let i; for (i = 0; i < x.length; i++) { if (x[i].style.visibility === "hidden") { x[i].style.visibility = "visible"; } else { x[i].style.visibility = "hidden"; }}}
                                let variable = document.getElementById("main").offsetTop;
                                let height = variable/1.33;
                                document.getElementById("team").style.top = height + "px";
    
                            </script>    
                              
                    <button onclick="myFunction()" class="button_show_red_only" align="center">SHOW RED ONLY</button>
                    </body></html>'''

    singleHtmlTestResult += '''</body></html>'''

    with open(dashboardHtmlFile, 'w') as template_file:
        template_file.write(htmlTestResults)
    with open(dashboardSingleHtmlTestFile, 'w') as template_file:
        template_file.write(singleHtmlTestResult)


def main():
    createHtmlTestResultReport()


if __name__ == "__main__":
    main()
