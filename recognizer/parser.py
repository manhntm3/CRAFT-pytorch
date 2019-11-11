import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag



def parse_email(email):
    # regex for check email from http://emailregex.com
    regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if re.search(regex, email):
        return email
    return None


def parse_phone(phone):
    """
    function to parse phone
    """
    
    #if phone contain character, make sure it's phone,dien thoai...etc
    common_phone_titles=[]
    with open("recognizer/recognizer_data/phone_recog.txt","r") as f:
        for phone_title in f:
            phone_title = phone_title.strip().lower()
            if len(phone_title):
                common_phone_titles.append(phone_title)
    phone = phone.replace("+","0")
    phone = phone.replace(":","").replace("(","").replace(")","").lower() 
    phone = re.sub('[!@#$%^&*()[]{};:,./<>?\|`~-=_]', '', phone)
    for phone_title in common_phone_titles:
        if phone.find(phone_title) >= 0:
            phone = re.sub('[^0-9]+', '', phone)
            phone = phone.replace(phone_title,"")
            phone = phone.replace(" ","")
            return phone
    #phone = re.sub('[^A-Za-z0-9]+', '', phone)
    
    phone = phone.replace(" ","")
    if not phone.isdigit():
        return None
    
    # regex for check phone from https://stackoverflow.com/questions/3868753/find-phone-numbers-in-python-script
    #regex = "\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}"
    # regex from http://www.regexlib.com/REDetails.aspx?regexp_id=73
    #regex = "^(\(?\+?[0-9]*\)?)?[0-9_\- \(\)]*$"
    #return re.search(regex, phone.replace(" ",""))
    return phone

def parse_info(infor):
    if all(c == ' ' for c in infor): return False
    return True
def parse_company(company):
    
    
    common_companies=[]
    with open("recognizer/recognizer_data/company_recog.txt","r") as f:
        for company_title in f:
            company_title = company_title.strip().lower()
            if len(company_title):
                common_companies.append(company_title)
    company = company.lower()
    for company_title in common_companies:
        if company.find(company_title) >= 0:
            return company
    #phone = re.sub('[^A-Za-z0-9]+', '', phone)
    # company name must be uppercase
    if company.upper() != company:
        return None
    return company

def parse_address(address):
    # check address contain number and character
    regex = ".*[0-9][a-z].*"
    
    if not re.search(regex, address):
        return None
    return address

def parse_website(website):
    
    # check website domain from https://stackoverflow.com/questions/6718633/python-regular-expression-again-match-url
    
    regex = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:\-_=#])*"
    if not re.search(regex, website):
        return None
    return website
def parse_name(name):
    #check if name contain equal or smaller than 5 words
    if len(name.split())>5: return None
    
    #check if length of the name smaller than 30 words
    if len(name)>30: return None
    
    #check if name not contain any digits
    if re.search(r'\d', name): return None
    
    #check if name not contain special characters
    #if re.match(r"[~\!@#\$%\^&\*\(\)_\+{}\":;'\[\]]", name ): return False
    if re.match(r'^[^*$<,>?!%[]\|\\?]*$',name): return None
    
    #check if pog_tag is all proper noun -> probably it's a name
    count = nltk.pos_tag(nltk.word_tokenize(name))
    count = [seq[1] for seq in count if seq[1]!='NNP']
    if len(count)!=0:
        return None      
    return name

if __name__ == '__main__':
    print(parse_company("base.vn"))
    print(parse_company("Immigration Law Group LLP"))
    
#     print(parse_phone("15396 N. 83rd Ave Suite D100, Peoria, AZ 85381-5627 USA"))
#     print(parse_phone("Điện thoại: 623-334-5513"))
#     print(parse_phone("(+64)933259 669"))
#     print(parse_phone("Điện Thoại Gọi Trực Tiếp: +1.410.970.6904"))
#     print(parse_phone("Phone: 408.632.9191"))
    