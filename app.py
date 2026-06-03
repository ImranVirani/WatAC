from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
app = Flask(__name__)

db = 'votes.db'

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
]

def init_db():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS data (
            building TEXT PRIMARY KEY,
            yes_votes INTEGER NOT NULL DEFAULT 0,
            no_votes INTEGER NOT NULL DEFAULT 0
        )
        '''
    )
    for building in DEFAULT_BUILDINGS:
        cursor.execute(
            'INSERT OR IGNORE INTO data (building, yes_votes, no_votes) VALUES (?, 0, 0)',
            (building,),
        )
    conn.commit()
    conn.close()


def get_buildings():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT building FROM data ORDER BY building')
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows or DEFAULT_BUILDINGS.copy()


def load_votes(building):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('SELECT yes_votes, no_votes FROM data WHERE building = ? LIMIT 1', (building,))
    row = cursor.fetchone()
    if row:
        yes_votes, no_votes = row
        votes['yes'] = yes_votes or 0
        votes['no'] = no_votes or 0
    else:
        votes['yes'] = 0
        votes['no'] = 0
    conn.close()


def update_vote(building, choice):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    if choice == 'yes':
        cursor.execute(
            'UPDATE data SET yes_votes = yes_votes + 1 WHERE building = ?',
            (building,),
        )
    elif choice == 'no':
        cursor.execute(
            'UPDATE data SET no_votes = no_votes + 1 WHERE building = ?',
            (building,),
        )
    if cursor.rowcount == 0:
        yes_votes = 1 if choice == 'yes' else 0
        no_votes = 1 if choice == 'no' else 0
        cursor.execute(
            'INSERT INTO data (building, yes_votes, no_votes) VALUES (?, ?, ?)',
            (building, yes_votes, no_votes),
        )
    conn.commit()
    conn.close()


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
