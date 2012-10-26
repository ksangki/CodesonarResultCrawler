# made by ppiazi@gmail.com
# Joohyun Lee
# Codesonar Result Crawler v0.1 (2012.10.21)
# History
#   2012.10.19  v0.1    Created
#   2012.10.22  v0.2    Change usage -> crc.exe [project_name] [xml_input_file]

import os,sys
import urllib2, urllib
import cookielib
import xlwt
from BeautifulSoup import BeautifulSoup

CODESONAR_HUB = "http://150.150.44.227:7340"
CODESONAR_HUB_LOGIN = "http://150.150.44.227:7340/sign_in.html"
codesonar_login_accounts = {
    'lig1':'lig1',
    'lig2':'lig2',
    'lig3':'lig3',
    'lig4':'lig4',
    'lig5':'lig5',
    'lig6':'lig6',
    'lig7':'lig7',
    'lig8':'lig8',
    'lig9':'lig9'
}

class CodeSonarResultCrawler:
    def __init__(self, project_name="result"):
        self._warning_list = []
        self._fail_warning_list = []
        self._cwd = os.getcwd()
        self._project_name = project_name
        self._codesonar_repository_path = self._cwd + "\\" + project_name + "\\"        
        self._cj = cookielib.CookieJar()
        self._opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self._cj))
        urllib2.install_opener(self._opener)

    def login_hub(self):
        login_success = False

        for userid in codesonar_login_accounts.keys():
            print "\tTry to login with %s" % (userid)
        
            login_data = urllib.urlencode({'sif_sign_in' : 'yes', 'sif_username' : userid, 'sif_password' : codesonar_login_accounts[userid]})
    
            try:
                req = urllib2.Request(CODESONAR_HUB_LOGIN, login_data)
                res = self._opener.open(req)
                print "\tSucceeded to login!!"
                login_success = True
                break
            except:
                print "\tFailed to login!!"

        return login_success

    def parse_xml(self, xml_file = "result.xml"):
        inx = 0
        f = open(xml_file, "r")
        xml_contents = f.read()
        self._bs = BeautifulSoup(xml_contents)

        # iterate all warnings and handle them
        warnings = self._bs('warning')
        for warning in warnings:
            wd = {}
            wd["cw_class"] = warning.find('class').string
            wd["cw_file"] = warning.find('file').string
            wd["cw_line_number"] = int(warning.find('line_number').string)
            wd["cw_procedure"] = warning.find('procedure').string

            # change url to html url
            temp_url = warning["url"]
            temp_url = temp_url[:warning["url"].find('?')]
            temp_url = temp_url.replace('xml', 'html')
            temp_url = CODESONAR_HUB + temp_url
            wd["cw_url"] = temp_url

            # change url to local url
            t_i = wd["cw_url"].rfind('/') + 1
            wd["cw_local_url"] = self._codesonar_repository_path + wd["cw_url"][t_i:]

            self._warning_list.append(wd)
            
            inx = inx + 1
        print "\t %d warinings are found." % (inx)

    def download_results(self):
        try:
            os.mkdir(self._codesonar_repository_path)
        except:
            pass

        total_count = len(self._warning_list)
        current_count = 1
        success_count = 0
        fail_count = 0
        
        #iterate all warining and download each html page
        for item in self._warning_list:
            print "\t(%d / %d) Downloading %s ..." % (current_count, total_count, item["cw_url"])
            req = urllib2.Request(item["cw_url"])
            try:
                res = self._opener.open(req)
                success_count = success_count + 1
            except:
                #if it fails to download a html, add it to fail list and handle it later
                print "%s Fail to download" % (item["cw_url"])
                self._fail_warning_list.append(item)
                fail_count = fail_count + 1
                continue

            #read a html and save it
            c = res.read()            
            f = open(item["cw_local_url"], "w")
            f.write(c)
            f.flush()
            f.close()

            current_count = current_count + 1

        print "\t (Success : %d / Fail : %d / Total : %d)" % ( success_count, fail_count, total_count )

        # if there is something missing(mainly because of network condition), save a missing list into a file.
        if fail_count != 0:
            fail_list_file_name = "%s_fail_list.txt" %(self._project_name)
            print "\t Check %s" % (fail_list_file_name)
            fail_list = self._cwd + "\\%s" % (fail_list_file_name)
            ff = open(fail_list, "w")
            for item in self._fail_warning_list:
                fail_file = "%s,%s,%d,%s,%s\n" % (item["cw_class"], item["cw_file"], item["cw_line_number"], item["cw_procedure"], item["cw_url"])
                ff.write(fail_file)
            ff.flush()
            ff.close()

    def make_report(self):     
        save_path = ".\\" + self._project_name + ".xls"

        #create an excel file
        wb = xlwt.Workbook('cp949')
        ws = wb.add_sheet('CodeSonar_result')

        #make titles
        row = 0
        ws.write(row, 0, "cw_class")
        ws.write(row, 1, "cw_file")
        ws.write(row, 2, "cw_line_number")
        ws.write(row, 3, "cw_procedure")
        ws.write(row, 4, "cw_url")
        ws.write(row, 5, "cw_local_url")

        #iterate and fill out data
        row = 1
        for item in self._warning_list:
            ws.write(row, 0, item["cw_class"])
            ws.write(row, 1, item["cw_file"])
            ws.write(row, 2, item["cw_line_number"])
            ws.write(row, 3, item["cw_procedure"])
            ws.write(row, 4, item["cw_url"])
            ws.write(row, 5, "file://" + item["cw_local_url"])

            row = row + 1

        #save
        wb.save(save_path)

def print_usage():
    print "crc.exe [project_name] [xml_input_file]"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_usage()
        os._exit(1)

    #get arguments
    project_name = sys.argv[1]
    input_xml = sys.argv[2]
    
    csrc = CodeSonarResultCrawler(project_name)
    print "[Login to HUB]"
    if csrc.login_hub() == False:
        print "All accounts are not available."
        os._exit(1)
    
    csrc.parse_xml(input_xml)
    print "[Making an Excel Report]"
    csrc.make_report()
    print "[Downloading codesonar results from HUB]"
    csrc.download_results()
    os._exit(0)
