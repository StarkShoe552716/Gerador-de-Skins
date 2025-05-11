import io
import zipfile
import json
import uuid
import os
import secrets
from flask import Flask, render_template, request, send_file, send_from_directory, jsonify

SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))

app = Flask(__name__)  
app.name = "McSkinsGenerator"
print(app.name)  

app.config['SECRET_KEY'] = SECRET_KEY  
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def gerador():
    return render_template('Skin.html')

@app.route('/generate', methods=['POST'])
def generate_pack():
    files = request.files.getlist('skins')
    new_names = request.form.getlist('name')
    display_names = request.form.getlist('display_name')
    localization_names = request.form.getlist('location')
    geometries = request.form.getlist('geometry')
    
    manifestName = request.form.get('manifestName', 'Custom skin pack')
    manifestDescription = request.form.get('manifestDescription', 'Pacote de skins gerado automaticamente.')
    lang_selected = request.form.get('lang', 'pt_br')
    manifestAuthor = request.form.get('manifestAuthor', 'PointyFour')

    if not files or not new_names or not display_names or not localization_names or not geometries:
        return jsonify({"error": "Certifique-se de preencher todos os campos corretamente!"}), 400

    manifest = {
        "format_version": 2,
        "header": {
            "name": manifestName,
            "description": manifestDescription,
            "uuid": str(uuid.uuid4()),
            "version": [1, 0, 0]
        },
        "modules": [
            {
                "type": "skin_pack",
                "uuid": str(uuid.uuid4()),
                "version": [1, 0, 0]
            }
        ],
        "metadata": {
            "authors": [manifestAuthor]
        }
    }

    skins_json = {
        "localization_name": "Skins",
        "serialize_name": "Skins",
        "skins": []
    }

    lang_lines = []
    lang_filename = f"texts/{lang_selected}.lang"

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=4))

        for f, nm, dname, loc_name, geom in zip(files, new_names, display_names, localization_names, geometries):
            if not f.filename.endswith('.png'):
                return jsonify({"error": "Apenas arquivos .png são permitidos"}), 400
            
            texture_path = f"{nm}.png"
            zf.writestr(texture_path, f.read())

            geometry_type = "geometry.humanoid.customSlim" if geom.lower() == "slim" else "geometry.humanoid.custom"

            skins_json["skins"].append({
                "geometry": geometry_type,
                "texture": texture_path,
                "type": "free",
                "localization_name": loc_name
            })

            lang_key = f"skin.Skins.{loc_name}"
            lang_lines.append(f"{lang_key}={dname}")

        zf.writestr("skins.json", json.dumps(skins_json, indent=4))
        zf.writestr(lang_filename, "\n".join(lang_lines))

    mem_zip.seek(0)
    return send_file(
        mem_zip,
        download_name="skin_pack.mcpack",
        as_attachment=True,
        mimetype="application/zip"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
