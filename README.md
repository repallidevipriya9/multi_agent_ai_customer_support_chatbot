# capstone-project-grp1

## Tto create the key-pai

`ssh-keygen -t rsa`    (copy the public file and add in Ssettings >> SSH Key on GitHub)

`git clone ....`

# To Ppublish the changes on Remote

`git status`

```
git add .
git commit -m "msg related to the changes made"
git push
```

`git pull`


# Activate the Virtual Environment

`venv\Scripts\activate`

#Open streamlit(frontend)
streamlit run frontend/streamlit_app.py

#open uvicorn
install pyton libararies - python install -r requirements.txt
uvicorn backend.app.main:app

#open n8n through command prompt - n8n start
