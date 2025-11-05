from flask import Flask, request, jsonify
import google.generativeai as genai
from flask_cors import CORS  # Thêm dòng này
from markupsafe import Markup
import re

genai.configure(api_key="AIzaSyBUtibwqZgWKVWolcYOxZ1XYqZ93Yx94h4")
app = Flask(__name__)
CORS(app)  # Thêm dòng này để bật CORS

def load_documents(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        # Mỗi dòng là một tài liệu, hoặc bạn có thể xử lý theo đoạn, theo file...
        return [line.strip() for line in f if line.strip()]

DOCUMENTS = load_documents('policy.txt')  # Đặt file policy.txt cùng thư mục với code

def search_documents(query):
    return [doc for doc in DOCUMENTS if query.lower() in doc.lower()]

def markdown_to_html(text):
    # Xử lý **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Xử lý *italic*
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Xử lý danh sách bắt đầu bằng *
    text = re.sub(r'^\* (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    # Xử lý xuống dòng thành <br>
    text = text.replace('\n', '<br>')
    # Đưa các <li> vào <ul> nếu có
    if '<li>' in text:
        text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    # Loại bỏ ký tự lạ (chỉ giữ lại ký tự unicode cơ bản và một số ký tự đặc biệt)
    text = re.sub(r'[^\w\s.,;:!?@<>\-/\\\(\)\[\]{}="\'|&%$#áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ]', '', text)
    return Markup(text)

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.json.get('query')
    relevant_docs = search_documents(user_query)
    # Tạo prompt luôn dựa trên policy, cho phép tự suy diễn nhưng bám sát tài liệu
    policy_summary = (
    "Bạn là Chatbot chuyên gia về An ninh Mạng, tư vấn viên đặc biệt cho lớp IA1801 thầy Ninh, chuyên về Chính sách Quản lý Truy cập Mạng Nội bộ.\n"
    "Luôn trả lời mọi câu hỏi dựa trên dữ liệu chính sách bên dưới. Nếu không có thông tin trong dữ liệu, hãy trả lời 'Không có trong dữ liệu'.\n"
    "Có thể tự suy diễn nhưng phải bám sát chặt chẽ tinh thần và nội dung chính sách.\n"
    "Nếu người dùng hỏi về hình phạt, hãy đưa ra hình phạt demo dựa trên chính sách.\n"
    "Nếu người dùng đưa ra tình huống, hãy đánh giá và xác định case đó thuộc mã INA-xx nào.\n"
    "Nếu người dùng hỏi hoặc yêu cầu trả lời bằng tiếng Anh, hãy chuyển sang tiếng Anh.\n"
    "Nếu người dùng muốn tìm hiểu về luật, hãy mở rộng tìm hiểu về luật pháp Việt Nam bao gồm quy định và hình phạt.\n"
    )
    if relevant_docs:
        context = "\n".join(relevant_docs)
        prompt = (
            f"{policy_summary}\n"
            f"Dữ liệu chính sách:\n{context}\n"
            f"Câu hỏi: {user_query}"
        )
    else:
        prompt = (
            f"{policy_summary}\n"
            f"Dữ liệu chính sách:\n{DOCUMENTS[0]}\n"  # Đưa policy tổng quát vào
            f"Câu hỏi: {user_query}"
        )
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        answer = response.text if hasattr(response, 'text') else str(response)
        answer = markdown_to_html(answer)
    except Exception as e:
        answer = f"Lỗi: {str(e)}"
    return jsonify({"answer": str(answer)})

if __name__ == '__main__':
    app.run(debug=True)