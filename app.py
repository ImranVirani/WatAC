from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_KEY / SUPABASE_PUBLISHABLE_KEY environment variables"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__)

votes = {'yes': 0, 'no': 0}
DEFAULT_BUILDINGS = [
    'Applied Health Sciences',
    'C2 Engineering Building',
    'Carl Pollock Hall',
    'Chemistry Building',
    'Davis Centre',
    'Dana Porter Library',
    'Earth Sciences Building',
    'Engineering 1',
    'Engineering 2',
    'Engineering 3',
    'Engineering 4',
    'Engineering 5',
    'Engineering 6',
    'Engineering 7',
    'Health Sciences',
    'Hagey Hall',
    'Humanities',
    'Math and Computer Building (MC)',
    'Natural Resources Building',
    'Quantum-Nano Centre',
    'Physical Activities Complex',
    'RCH Hall',
    'St. Paul’s University College',
    'Student Life Centre',
    'Tatham Centre',
    'Village 1',
    'Village 2',
    'Village 3',
    'Mathematics 3'
]
TABLE_NAME = 'data'

def raise_if_error(response, action=None):
    if getattr(response, 'error', None):
        action_name = action or 'Supabase request'
        raise RuntimeError(f"{action_name} failed: {response.error}")


def init_db():
    rows = [
        {
            'building': building,
            'yes_votes': 0,
            'no_votes': 0,
        }
        for building in DEFAULT_BUILDINGS
    ]
    response = supabase.table(TABLE_NAME).upsert(rows, on_conflict='building').execute()
    raise_if_error(response)


def get_buildings():
    response = supabase.table(TABLE_NAME).select('building').execute()
    if getattr(response, 'error', None):
        raise_if_error(response, 'select buildings')

    rows = getattr(response, 'data', []) or []
    buildings = sorted({row.get('building') for row in rows if row.get('building')})
    return buildings or DEFAULT_BUILDINGS.copy()


def load_votes(building):
    response = supabase.table(TABLE_NAME).select('yes_votes,no_votes').eq('building', building).execute()
    if getattr(response, 'error', None):
        raise_if_error(response, 'load votes')
    if not getattr(response, 'data', []):
        votes['yes'] = 0
        votes['no'] = 0
        return

    row = response.data[0]
    votes['yes'] = row.get('yes_votes', 0) or 0
    votes['no'] = row.get('no_votes', 0) or 0


def update_vote(building, choice):
    response = supabase.table(TABLE_NAME).select('yes_votes,no_votes').eq('building', building).execute()
    existing = getattr(response, 'data', []) or []

    if existing:
        current = existing[0]
        yes_votes = current.get('yes_votes', 0) or 0
        no_votes = current.get('no_votes', 0) or 0
    else:
        yes_votes = 0
        no_votes = 0

    if choice == 'yes':
        yes_votes += 1
    elif choice == 'no':
        no_votes += 1
    else:
        return

    response = supabase.table(TABLE_NAME).upsert(
        {
            'building': building,
            'yes_votes': yes_votes,
            'no_votes': no_votes,
        },
        on_conflict='building',
    ).execute()
    raise_if_error(response, 'update vote')


init_db()
load_votes('Building A')
@app.route('/', methods=['GET'])
def home():
    selected_building = request.args.get('building', 'Building A')
    buildings = get_buildings()
    if selected_building not in buildings:
        selected_building = buildings[0]
    load_votes(selected_building)
    total = votes['yes'] + votes['no']
    return render_template(
        'index.html',
        votes=votes,
        total=total,
        buildings=buildings,
        selected_building=selected_building,
    )

@app.route('/vote', methods=['POST'])
def vote():
    choice = request.form.get('choice')
    building = request.form.get('building', 'Building A')
    if choice in votes:
        update_vote(building, choice)
        load_votes(building)
    return redirect(url_for('home', building=building))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug, host='0.0.0.0', port=port)
