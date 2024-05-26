import dash
import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, dcc
import pandas as pd
import joblib
import plotly.express as px
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import emoji
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, LabelEncoder
from sklearn.model_selection import train_test_split
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import VotingClassifier

class CustomTransformer(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.stopwords_arabic = set(stopwords.words('arabic'))

    def fit(self, X, y=None):
        # Add code for fitting the transformer here
        return self

    def transform(self, X):
        transformed_X = X.copy()
        transformed_X = X.apply(self.clean_txt)
        return transformed_X

    def clean_txt(self, text):
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' ', text)

        # Remove usernames starting with @
        text = re.sub(r'@[\w_]+', ' ', text)

        # Remove English words
        text = re.sub(r'\b[a-zA-Z]+\b', ' ', text)

        # Remove emojis
        text = re.sub(r'[\U00010000-\U0010ffff]', ' ', text)
        text = re.sub(r':[a-z_]+:', ' ', text)

        # Remove special characters
        text = re.sub('[*?!#@]', ' ', text)

        # Remove redundant percentage and bar lines
        text = re.sub(r'\|\|+\s*\d+%\s*\|\|+?[_\-\.\?]+', ' ', text)

        text = re.sub(r'[_\-\.\"\:\;\,\'\،\♡\\\)/(\&\؟]', ' ', text)

        # Remove digits
        text = re.sub(r'\d+', ' ', text)

        text_tokens = text.split()

        # filtered_text = [word for word in text_tokens if word not in self.stopwords_arabic]
        filtered_text = text_tokens
        # Split and rejoin
        text = ' '.join(filtered_text)

        return text

    def fit_transform(self, X, y=None):
        # This function combines fit and transform
        self.fit(X, y)
        return self.transform(X)

# Initialize Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.SLATE])

# Load the pre-trained model
loaded_pipeline = joblib.load('voting_pipeline_new.pkl')

# Define the layout of the app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("تخمين اللهجات العربية",  style={'textAlign': 'center', 'marginBottom': '30px', 'color': 'goldenrod', 'fontWeight': 'bold'})
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.H2("(مصري - لبناني - ليبي - مغربي - سوداني)",  style={'textAlign': 'center', 'marginBottom': '30px', 'color': 'goldenrod', 'fontWeight': 'bold'})
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Textarea(
                id="text-input",
                placeholder="Enter your text here",
                style={"width": "100%", "height": "200px"},
                className="mb-3"
            ),
            dbc.Button("تخمين", id="predict-button", color="light", size="lg", className="d-grid gap-2 col-6 mx-auto"),
            html.Div(id="prediction-alert"),
            html.Button("مسح", id="reset-button", n_clicks=0, className="d-grid gap-2 col-6 mx-auto mt-3", style={"fontSize": "20px"})
        ], width=6),
        dbc.Col([
            dcc.Graph(id="probability-graph")
        ], width=6)
    ])
])

# Define the callback to update the graph and display prediction alert
@app.callback(
    [Output("probability-graph", "figure"),
     Output("prediction-alert", "children"),
     Output("text-input", "value")],
    [Input("predict-button", "n_clicks"),
     Input("reset-button", "n_clicks")],
    [State("text-input", "value")]
)
def update_output(predict_clicks, reset_clicks, text):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "predict-button" and (predict_clicks is None or text is None or text.strip() == ""):
        return dash.no_update, None, text
    elif button_id == "predict-button":
        # Process the input text
        text_series = pd.Series([text])
        probabilities = loaded_pipeline.predict_proba(text_series)

        target_labels = ['EG', 'LB', 'LY', 'MA', 'SD']
        target_names = ['مصري', 'لبناني', 'ليبي', 'مغربي', 'سوداني']
        label_name_mapping = dict(zip(target_labels, target_names))
        class_labels = loaded_pipeline.classes_

        prob_dict = {label_name_mapping[label]: prob for label, prob in zip(class_labels, probabilities[0])}
        final_prediction_label = loaded_pipeline.predict(text_series)[0]
        final_prediction_name = label_name_mapping[final_prediction_label]

        labels = list(prob_dict.keys())
        probs = list(prob_dict.values())

        fig = px.bar(x=labels, y=probs, labels={'x': 'الدولة', 'y': 'الاحتمال'}, title='احتمال التخمين')

        fig.update_traces(marker_color=['green' if label == final_prediction_name else 'blue' for label in labels])

        alert = dbc.Alert(f"التنبؤ: {final_prediction_name}", color="info", className="d-grid gap-2 col-6 mx-auto", style={'textAlign': 'center', 'marginBottom': '30px', 'color': 'black', 'fontWeight': 'bold', 'fontSize': '20px'})

        return fig, alert, text
    elif button_id == "reset-button":
        return {}, None, ""
    else:
        return dash.no_update, None, text


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
