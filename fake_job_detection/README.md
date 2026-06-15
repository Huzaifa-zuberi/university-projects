# Fake Job Detection in Pakistan

Predicts whether a job posting is **Real** or **Fake** using machine learning.
Stack: **HTML, CSS, JavaScript, Flask, PostgreSQL (Supabase), Scikit-Learn**.

## Folder structure
```
fake_job_detection/
├── database.sql              # Supabase tables (users + predictions)
├── requirements.txt          # Python libraries
├── data/                     # put your dataset here -> fake_jobs_dataset.csv
├── notebook/                 # training + evaluation notebooks
├── model/                    # best_model.pkl appears here AFTER you run training
├── backend/                  # Flask app (config, database, auth, model_utils, app)
└── frontend/                 # (added in the next phase)
```

## Run order

1. **Install libraries**
   ```
   pip install -r requirements.txt
   ```

2. **Add your dataset**
   - Put your CSV in the `data` folder.
   - Open `notebook/model_training.ipynb` and check the **Settings** cell:
     `DATASET_PATH`, `TARGET_COL`, and `TEXT_COLS` must match your file.

3. **Train the model**
   - Run all cells in `model_training.ipynb`. This creates `model/best_model.pkl`
     and `model/model_results.json`.
   - Run `model_evaluation.ipynb` to see Accuracy, Precision, Recall, F1, and the confusion matrix.

4. **Create the database**
   - In Supabase, open the SQL Editor, paste `database.sql`, and click Run.

5. **Add your database details**
   - Open `backend/config.py` and fill in your Supabase connection values.

6. **Start the app**
   ```
   cd backend
   python app.py
   ```
   Open http://127.0.0.1:5000

> Note: the website pages (frontend) are added in the next phase. The backend and
> model are complete and the `/predict` route already works.

## Disclaimer
This is an academic awareness tool. A "Real" result does not guarantee a job is
genuine — always apply caution when sharing personal information online.
