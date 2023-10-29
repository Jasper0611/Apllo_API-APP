from flask import Flask, render_template, request, send_file 
import requests
import pandas as pd
import os

app= Flask(__name__)

@app.route("/")
def home():
    return render_template('index.html')

UPLOAD_FOLDER = 'c:\\Users\\innoppl\\VS Code\\uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# @app.route('/upload', methods=['POST', "GET"])
# def upload_csv():
#     if 'csvFile' in request.files:
#         csv_file = request.files['csvFile']
#         df = pd.read_csv(csv_file)
#         data=df[['Website', 'Country', 'Company' ]]

#         updated_file_path = f"{app.config['UPLOAD_FOLDER']}/updated_file.csv"
#         data.to_csv(updated_file_path, index=False)

#         return 'File uploaded and processed. <a href="/download">Download the updated file</a>'

#     return 'No valid CSV file uploaded.'

def apollo(api_key, url, domains):
    comp= []
    for company in domains:
        querystring = {
            "api_key": api_key,
            "domain": company
        }

        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, params=querystring)
        try:
            org = response.json()
            a = org['organization']
            company_info = {
                    'Company_URL_Passed':company,
                    'Company name': a.get('name', 'NA'),
                    'Website URL': a.get('website_url', 'NA'),
                    'industry': a.get('industry','NA'),
                    'City': a.get('city', 'NA'),
                    'State': a.get('state', 'NA'),
                    'Country': a.get('country', 'NA'),
                    'Annual Revenue': a.get('annual_revenue_printed', 'NA'),
                    'No Employees':a.get('estimated_num_employees','NA'),
                    'Phone': a.get('phone', 'NA'), 'Status': True
                }
            comp.append(company_info)
        except:
            comp.append({
                'Company_URL_Passed':company,
                'Company name': 'NA',
                'Website URL': 'NA',
                'City': 'NA',
                'State': 'NA',
                'Country': 'NA',
                'Annual Revenue': 'NA',
                'No Employees':'NA',
                'Phone': 'NA', 'Status': False
                })
    data=pd.DataFrame(comp)
    return data


def filtering(data):
    comp_info_available= data[data['Status']==1]
    US_comp = comp_info_available[comp_info_available['Country']=='United States']
    domains= US_comp['Company_URL_Passed']
    return domains

def contact_profiling(domains):
    people_search='https://api.apollo.io/v1/mixed_people/search'
    contact=[]
    for domain in domains:
        params={'q_organization_domains':domain,
           "api_key":api_key}
        headers = {
            'Cache-Control': 'no-cache',
        }
        response=requests.get(people_search, params=params,headers=headers)
        data=response.json()

        if data['people']:
            a=data['people']
            for i in range(len(a)):
                company=a[i]['organization']['name']
                website=a[i]['organization']['website_url']
                state=a[i].get('state', 'NA')
                city=a[i].get('city','NA')
                country=a[i].get('country','NA')
                first_name=a[i]['first_name']
                Last_name = a[i]['last_name']
                linkedin= a[i]['linkedin_url']
                title=a[i]['title']
                seniority= a[i].get('seniority','NA')
                email=a[i]['email']
                contact.append({'Company_URL_Passed': domain, 'company':company,'website':website,
                    'first_name':first_name, 'Last_name':Last_name,
                    'title':title ,'seniority':seniority,'email':email,'linkedin':linkedin,
                    'Contact city':city,'Contact state':state,'Contact country':country,'Status':True
                    })
        else:
            contact.append({'Company_URL_Passed': domain,'company':'NA','website':'NA',
                    'first_name':'NA', 'Last_name':'NA',
                    'title':'NA' ,'seniority':'NA','email':'NA','linkedin':'NA',
                    'Contact city':'NA','Contact state':'NA','Contact country':'NA','Status':False
                    })
    contants_profiled= pd.DataFrame(contact)
    return contants_profiled

def contact_filtering(contacts_profiled,data,Hirearchy ):
    US_contacts= contacts_profiled[contacts_profiled['Contact country']=='United States']
    contains_email= US_contacts[US_contacts['email'].notnull()]
    # Hirearchy = ['manager', 'c_suite', 'director','vp','founder','owner']
    filterd_Hirearchy ='|'.join(Hirearchy)
    targeted_seniority=contains_email[contains_email['seniority'].str.contains(filterd_Hirearchy, case=False, na=False)]
    titles= ['CEO', 'General Manager', 'Owner', 'Founder', 'President',
         'Marketing','Information Technology', 'IT', 'CMO', 'CTO',
        'operation', 'COO', 'Business Development', 'Ecommerce', 'E-commerce','CIO']
    filterd_titles ='|'.join(rf'\b{word}\b' for word in titles)
    targeted_contacts= targeted_seniority[targeted_seniority['title'].str.contains(filterd_titles, case=False, na=False)]
    merged_contacts= pd.merge(data,targeted_contacts , on='Company_URL_Passed')
    return merged_contacts

api_key="urLasOpQ9dxlUucvgcK_hw"
url = "https://api.apollo.io/v1/organizations/enrich"

@app.route('/upload', methods=['POST', "GET"])
def upload_csv():
    if 'csvFile' in request.files:
        csv_file = request.files['csvFile']
        df = pd.read_csv(csv_file)
        companies=df['URL']
        data=apollo(api_key,url,companies)
        comp_domains=filtering(data)
        contacts_profiled= contact_profiling(comp_domains)
        Hirearchy = request.form.getlist('userRole[]')
        final_data=contact_filtering(contacts_profiled,data,Hirearchy)
        updated_file_path = f"{app.config['UPLOAD_FOLDER']}/test_file.csv"
        final_data.to_csv(updated_file_path, index=False)
        return 'File uploaded and processed. <a href="/download">Download the updated file</a>'
    return 'No valid CSV file uploaded.'



@app.route('/download')
def download_updated_file():
    updated_file_path = f"{app.config['UPLOAD_FOLDER']}/test_file.csv"
    return send_file(updated_file_path, as_attachment=True, download_name='test_file.csv')

if __name__=="__main__":
    app.run(host="0.0.0.0", port=4000)
