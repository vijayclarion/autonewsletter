#create new enviourment
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt


#exiting env
cd PathToRAGMethodFolder
.\.venv\Scripts\activate.bat

python src\main.py input\Tech-Office-AllHandsMeeting_Nov.vtt  input\Monitoring_Systems_Overview_and_Comparison_Nov.pptx --title "Nov Newsletter for Monitoring systems"