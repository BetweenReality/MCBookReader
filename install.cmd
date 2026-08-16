pip install -r requirements.txt
pip install pyinstaller

@REM pyinstaller --icon=resources/images/written_book.ico --noconfirm ./bookreader.py
pyinstaller --noconfirm ./build.spec