from flask import Flask, render_template, request

app = Flask(__name__)

def calculate_bmi(weight, height):
    height_meters = height / 100
    bmi = weight / (height_meters ** 2)
    return bmi

def interpret_bmi(bmi):
    # 解釋函數與之前相同，這裡省略不寫

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        bmi = calculate_bmi(weight, height)
        interpretation = interpret_bmi(bmi)
        return render_template('result.html', bmi=bmi, interpretation=interpretation)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
