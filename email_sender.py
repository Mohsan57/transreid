import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import db_models
import tracemalloc
tracemalloc.start() 
sender_email = "campus.surveillance.system@gmail.com"
password = "bfomqqctqfobtgta"
def send_email(receiver_email, user_name, video_link):
  
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Your video for person identification has been processed"

    
    
    html = '''<!DOCTYPE html>
    <html" lang="en">
  <body class="u-body u-xl-mode" data-lang="en"><header class="u-clearfix u-container-align-center u-header u-header" id="sec-aa46"><div class="u-clearfix u-sheet u-sheet-1">
        <a href="https://nicepage.com" class="u-image u-logo u-image-1">
          <img src="images/default-logo.png" class="u-logo-image u-logo-image-1">
        </a>
      </div></header>
    <section class="" id="sec-2592">
      <div class="">
        <h3 class=""> Dear {username},
        </h3>
        <p class="u-align-left u-text u-text-2">We are pleased to inform you that the video you submitted for person identification on our website has been processed and is now ready for download. <br>
          <br>Please click on the following link to download your video:<br>
        </p>
        <a href="http://127.0.0.1:8000/video-reid/download_video/{videolink}" class="">Download Video</a>
        <p class="u-align-left u-text u-text-3"> Thank you for using our website for your person identification needs. <br>
          <br>Best regards, <br>Campus Sureivllance system
        </p>
      </div>
    </section>
    
    
    <footer class="u-align-center u-clearfix u-container-align-center u-footer u-grey-80 u-footer" id="sec-56dc"><div class="u-clearfix u-sheet u-sheet-1">
        <a href="" class="">Campus Surveillance System</a>
      </div>
    </footer>
  
</body></html>
    '''.format(username = user_name, videolink = video_link)
    # html = templates.TemplateResponse("email_template.html", data)
    message.attach(MIMEText(html, "html"))
    text = message.as_string()
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
    return {"message": "Email sent successfully"}
  

# send_email(None,"mohsanyaseen.dev@gmail.com", "mohsan", "google.com")