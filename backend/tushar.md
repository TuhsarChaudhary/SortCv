

user login -> dashboard -> long listing and short listing

# long listing -> pdf upload -> submit

table -> pdf name, id, pdf path, csv path, uploaded by, long_listing_csv, short_listing_csv, job_desc_path

- BACKEND
    - If pdf name exist in table pdf for that user
      thn skip the processing part
      (optional : pdf name same and size same)
    - else upload the pdf in s1 and save the path in s1
      and call the module function
        got df and will convert it in csv and save that in s1
        save the csv path in table

        return to json formatted csv

<!-- USER can do filters on long listing (frontend) -->

clicked on move to short listing
## api "save_long_listing_csv": final filter csv uplaod to s1 and save in table pdf

# SHORT LISTING
<!-- move to short listing handled by frontend -->

<!-- job desc pdf uploaded -> form to enter weights and filters -> -->
and click submit

api "short_listing" : data -> pdf file, weights, filters
        api save job desc pdf path file in table pdf and upload the jdpdf in s1

        get the final filter file using the path from the table and pass it to the
        module function along with weights and filters

        upload this new short_listing_csv file in s1 and save its path on pdf table

        module function return df and job description
        which we return to the frontend in json format


TO IMPROVE : can use celery to upload csv and pdfs
                or
             compress files properly


table -> model

table -> pdf_name, id, pdf_path, csv_path, uploaded_by(fk to user), long_listing_csv, short_listing_csv, job_desc_path

1. pdfname, id(auto),  pdf_path, csv_path, uploaded_by, "", "", ""

2. pdfname, id(auto),  pdf_path, csv_path, uploaded_by, long_listing_csv, "", ""

3. pdfname, id(auto),  pdf_path, csv_path, uploaded_by, long_listing_csv, "", job_desc

4. pdfname, id(auto),  pdf_path, csv_path, uploaded_by, long_listing_csv, short_listing_csv, job_desc

----

admin wala question?

user logged in -> login api called -> success return -> redirect to dashboard (frontend)

when dashboard open it will call the profile api (frontend)

profile api will return username, is_admin, phone number

home dashboard -> profile api called -> if profile api returns user details along with session details

login page redirect krdo dashboard pr usertable data ms 0.01

