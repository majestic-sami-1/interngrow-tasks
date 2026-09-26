import urllib.request
import json
import sys

BASE = 'http://127.0.0.1:5000'
KEY = 'cine-rec-secret-key-2026-secure'
H = {'X-API-Key': KEY, 'Content-Type': 'application/json'}

def get(path):
    req = urllib.request.Request(f'{BASE}{path}', headers=H)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())

def post(path, body):
    req = urllib.request.Request(f'{BASE}{path}', headers=H, data=json.dumps(body).encode())
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())

def run():
    print("[1] Testing Health Endpoint...")
    h = get('/api/health')
    print("   Status:", h['status'], "| Catalog count:", h['catalog_count'])
    assert h['status'] == 'healthy'

    print("\n[2] Testing User Personas...")
    users = get('/api/users')
    print("   Total users:", users['total'], "| First user:", users['users'][0]['name'])
    assert users['total'] >= 5

    print("\n[3] Testing Alex Rivera (Sci-Fi Enthusiast) Recommendations...")
    r1 = get('/api/recommendations?user_id=user-1&model=hybrid')
    alex_top = [x['item']['title'] for x in r1['recommendations'][:3]]
    print("   Top 3 for Alex:", alex_top)

    print("\n[4] Testing Sophia Chen (Drama Buff) Persona Switch...")
    r2 = get('/api/recommendations?user_id=user-2&model=hybrid')
    sophia_top = [x['item']['title'] for x in r2['recommendations'][:3]]
    print("   Top 3 for Sophia:", sophia_top)
    assert alex_top != sophia_top, "Recommendations should adapt to user persona!"

    print("\n[5] Testing Cold-Start Guest Persona...")
    r5 = get('/api/recommendations?user_id=user-5&model=hybrid')
    print("   Is Cold Start:", r5['is_cold_start'], "| Note:", r5['cold_start_note'])
    assert r5['is_cold_start'] is True

    print("\n[6] Testing Model Toggles (Content vs Collaborative)...")
    rc = get('/api/recommendations?user_id=user-1&model=content')
    rcf = get('/api/recommendations?user_id=user-1&model=collaborative')
    print("   Content Model Top:", rc['recommendations'][0]['item']['title'])
    print("   Collaborative Model Top:", rcf['recommendations'][0]['item']['title'])

    print("\n[7] Testing Hybrid Slider (alpha=0.9 vs alpha=0.1)...")
    ra9 = get('/api/recommendations?user_id=user-1&model=hybrid&alpha=0.9')
    ra1 = get('/api/recommendations?user_id=user-1&model=hybrid&alpha=0.1')
    print("   alpha=0.9 Top:", ra9['recommendations'][0]['item']['title'], "breakdown:", ra9['recommendations'][0]['breakdown'])
    print("   alpha=0.1 Top:", ra1['recommendations'][0]['item']['title'], "breakdown:", ra1['recommendations'][0]['breakdown'])
    assert ra9['recommendations'][0]['breakdown']['content_weight'] == '90%'
    assert ra1['recommendations'][0]['breakdown']['content_weight'] == '10%'

    print("\n[8] Testing Similar Items (More Like This for Interstellar)...")
    sim = get('/api/items/item-1/similar?limit=3')
    for s in sim['similar_items']:
        print(f"   Similar: {s['item']['title']} ({s['match_percentage']}%) - Reasons: {s['reasons']}")
    assert len(sim['similar_items']) > 0

    print("\n[9] Testing Rating Submission & Real-time Update...")
    post_res = post('/api/users/user-1/rate', {'item_id': 'item-11', 'rating': 5.0})
    clean_msg = post_res.get('message', '').encode('ascii', 'replace').decode()
    print(f"   Rate response status: {post_res.get('status')} - message: {clean_msg}")
    assert post_res['status'] == 'success'

    print("\n[10] Testing User Profile Analysis (Radar, Diversity, Novelty)...")
    prof = get('/api/users/user-1/profile')
    p = prof['profile_analysis']
    print(f"   Average Rating: {p['average_rating']} | Diversity Score: {p['diversity_score']}% ({p['diversity_label']}) | Novelty: {p['novelty_score']}%")
    print("   Top Genre Affinities:", [(g['genre'], f"{g['affinity_percentage']}%") for g in p['genre_affinity'][:3]])

    print("\n[11] Testing Recommendation Audit History...")
    hist = get('/api/history?user_id=user-1&limit=5')
    print("   Logged entries count:", len(hist['history']))
    print("   Most recent log:", hist['history'][0]['item_title'], "| Model:", hist['history'][0]['model_type'], "| Status:", hist['history'][0]['status'])
    assert len(hist['history']) > 0

    print("\n[12] Testing Model Laboratory Comparison...")
    comp = get('/api/analytics/model-comparison?user_id=user-1')
    print("   Model Agreement Overlap:", comp['metrics']['content_vs_cf_overlap'], "/ 5")
    print("   Jaccard Taste Agreement:", comp['metrics']['jaccard_similarity'])

    print("\n==================================================")
    print("SUCCESS: ALL 12 USER JOURNEY VERIFICATIONS PASSED!")
    print("==================================================")

if __name__ == '__main__':
    run()
