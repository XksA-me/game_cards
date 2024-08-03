from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from models import db, Card
import os
from PIL import Image
import io
from paddleocr import PaddleOCR, draw_ocr

'''
作者：老表
微信公众号：简说Python
个人微信：pythonbrief
欢迎学习交流
'''

# 初始化PaddleOCR，选择识别模型
# use_angle_cls=True 适用于方向分类，lang='ch' 用于中英文识别
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate = Migrate(app, db)


def paddle_ocr(image_path, ocr):
    # 读取图像
    img = Image.open(image_path)

    # 进行OCR识别
    result = ocr.ocr(image_path)
    # print("识别结果：", result[0][0][1][0])
    # print("可信度：", result[0][0][1][1])
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # 图片
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                print("filename", filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                result = paddle_ocr(filepath, ocr)
                os.remove(filepath)  # 识别后删除上传的文件
                try:
                    text = result[0][0][1][0]
                except Exception as e:
                    print(f"【ocr出错】{e}\n【result】{result}")
                return render_template('upload.html', text=text)
        # 文本
        if 'content' in request.form:
            content = request.form['content']
            for card_content in content.split('\n'):
                if card_content.strip():
                    new_card = Card(content=card_content.strip())
                    db.session.add(new_card)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/export')
def export():
    cards = Card.query.all()
    output = io.StringIO()
    for card in cards:
        output.write(f"{card.content}\n")
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), download_name='cards.txt', as_attachment=True)

@app.route('/display')
def display():
    cards = Card.query.all()
    return render_template('display.html', cards=cards)

if __name__ == '__main__':
    app.run(port=5002, debug=False)
