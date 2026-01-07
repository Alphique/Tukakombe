from flask import request

def log_requests(app):
    @app.before_request
    def log_request_data():
        if request.method == "POST":
            print("\n===== INCOMING POST REQUEST =====")
            print("URL:", request.path)

            print("\nFORM DATA:")
            for k, v in request.form.items():
                print(f"{k}: {v}")

            print("\nFILES:")
            for f in request.files:
                print(f"{f} -> {request.files[f].filename}")

            print("===== END REQUEST =====\n")
