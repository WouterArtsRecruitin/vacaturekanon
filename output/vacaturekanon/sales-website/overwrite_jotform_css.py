import requests

api_key = "8446b2ba4c0c9cc79355873c4479d269"
form_id = "260757174181359"
url = f"https://eu-api.jotform.com/form/{form_id}/properties?apiKey={api_key}"

css_code = """
/* VACATUREKANON V2 DARK MODE OVERRIDE */
html.supernova, body.supernova, .supernova, .jotform-form, .form-all, .form-section.page-section {
    background-color: #07050f !important;
    background-image: none !important;
    background: #07050f !important;
    box-shadow: none !important;
}
.form-all {
    margin-top: 0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.form-label, .form-label-top, .form-label-left, .form-label-right, .form-html, .form-header, .form-subHeader, label {
    color: #ffffff !important;
    font-weight: 600 !important;
    text-shadow: none !important;
}
.form-subHeader, .form-sub-label, .form-line-error-words {
    color: #a1a1aa !important;
}
.form-dropdown, .form-textarea, .form-textbox, .form-radio-other-input, .form-checkbox-other-input, .form-matrix-table td {
    background-color: #120d2a !important;
    background: #120d2a !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
.form-dropdown:focus, .form-textarea:focus, .form-textbox:focus {
    border-color: #ff00cc !important;
    box-shadow: 0 0 10px rgba(255,0,204,0.3) !important;
    outline: none !important;
}
.form-submit-button {
    background: linear-gradient(90deg, #FF5500, #ff00cc) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 100px !important;
    padding: 15px 30px !important;
    font-weight: 800 !important;
    font-size: 16px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    cursor: pointer !important;
    width: 100% !important;
    max-width: 100% !important;
    margin-top: 20px !important;
    transition: transform 0.3s ease !important;
}
.form-submit-button:hover {
    transform: scale(1.03) !important;
}
.form-line-active {
    background-color: transparent !important;
}
"""

try:
    payload = {"properties[injectCSS]": css_code}
    resp = requests.post(url, data=payload)
    print("STATUS:", resp.status_code)
except Exception as e:
    print(f"Error: {e}")
