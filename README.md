
# From Code to Image

This project aims at creating a webstite which can convert your python code into a nice looking image. You can choose among plenty of the regular vs styles and even load your code from a GitHub repository. Additionally there is an authentication system which requires a mail to log in the site. Finally all the infotmation about the user is saved into a csv file which can be accessed with the /export route.




## 🖥️ Structure of Directory

- static/
    - styles.css

- templates/
    - base.html
    - code_input.html
    - image.html
    - style_selection.html
    - form.html
- app.py
- utils.py
- .env
- .gitignore
- requirements.txt


## ⚠️ Requirements
To install all the required libraries simply execute this command:

```bash
  pip install -r requirements.txt
```

## 🔋 Running the Website

To run the website you must activate the python server with flask:

```terminal
  pyton .\app.py
```


## 🚀 About Me
I'm a high-school student just sharing my projects and my passion is informatics
