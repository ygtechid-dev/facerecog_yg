from flask import Flask, request, jsonify
from deepface import DeepFace
import os
import uuid
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Tentukan direktori untuk menyimpan wajah yang diregistrasi
REGISTERED_FACES_DIR = 'registered_faces'

# Pastikan direktori untuk wajah yang diregistrasi ada
if not os.path.exists(REGISTERED_FACES_DIR):
    os.makedirs(REGISTERED_FACES_DIR)

def save_base64_image(base64_string, filepath):
    """Simpan gambar dari string base64 ke file"""
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    image.save(filepath)

@app.route('/register-face', methods=['POST'])
def register_face():
    data = request.get_json()

    if 'image_base64' not in data:
        return jsonify({'error': 'Gambar base64 tidak ditemukan dalam request'}), 400

    image_base64 = data['image_base64']

    # Ambil nama file khusus dari request, atau gunakan UUID jika tidak ada
    desired_filename = data.get('filename', f"{uuid.uuid4()}.jpg")

    # Pastikan nama file memiliki ekstensi .jpg jika belum ada
    if not desired_filename.lower().endswith('.jpg'):
        desired_filename += '.jpg'

    # Gabungkan dengan path direktori
    filepath = os.path.join(REGISTERED_FACES_DIR, desired_filename)

    # Simpan gambar dari data base64
    save_base64_image(image_base64, filepath)

    return jsonify({'message': 'Wajah berhasil diregistrasi', 'filename': desired_filename}), 200

@app.route('/verify-face', methods=['POST'])
def verify_face():
    data = request.get_json()

    if 'image_base64' not in data:
        return jsonify({'error': 'Gambar base64 tidak ditemukan dalam request'}), 400

    image_base64 = data['image_base64']
    temp_filename = f"temp_{uuid.uuid4()}.jpg"
    temp_filepath = os.path.join(REGISTERED_FACES_DIR, temp_filename)

    # Simpan gambar sementara dari data base64
    save_base64_image(image_base64, temp_filepath)

    try:
        matched = False
        matched_filename = None

        for registered_image in os.listdir(REGISTERED_FACES_DIR):
            registered_filepath = os.path.join(REGISTERED_FACES_DIR, registered_image)
            result = DeepFace.verify(img1_path=temp_filepath, img2_path=registered_filepath, enforce_detection=False)

            if result['verified']:
                matched = True
                matched_filename = registered_image
                break

        os.remove(temp_filepath)  # Hapus file sementara setelah verifikasi selesai

        if matched:
            return jsonify({'message': 'Wajah cocok dengan wajah terdaftar', 'matched_with': matched_filename}), 200
        else:
            return jsonify({'message': 'Wajah tidak cocok dengan wajah manapun'}), 404

    except Exception as e:
        os.remove(temp_filepath)  # Pastikan file sementara dihapus meskipun terjadi error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
