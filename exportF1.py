import os
from dotenv import load_dotenv
import pandas as pd
from googleapiclient.discovery import build

# Carrega API_KEY de .env
load_dotenv()
API_KEY     = os.getenv('YOUTUBE_API_KEY')
PLAYLIST_ID = 'PLfoNZDHitwjUv0pjTwlV1vzaE0r7UDVDR'

def get_playlist_video_ids(youtube, playlist_id):
    ids, token = [], None
    while True:
        resp = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=token
        ).execute()
        # cada item tem resourceId.videoId
        ids += [
            item['snippet']['resourceId']['videoId']
            for item in resp['items']
        ]
        token = resp.get('nextPageToken')
        if not token:
            break
    return ids

def get_videos_details(youtube, ids):
    rows = []
    for i in range(0, len(ids), 50):
        resp = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(ids[i:i+50])
        ).execute()
        for v in resp['items']:
            s = v['statistics']
            rows.append({
                'videoId':      v['id'],
                'title':        v['snippet']['title'],
                'publishedAt':  v['snippet']['publishedAt'],
                'viewCount':    int(s.get('viewCount', 0)),
                'likeCount':    int(s.get('likeCount', 0)),
                'commentCount': int(s.get('commentCount', 0)),
            })
    return rows

def main():
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    ids     = get_playlist_video_ids(youtube, PLAYLIST_ID)
    data    = get_videos_details(youtube, ids)
    

    # Cria DataFrame e exporta CSV
    df = pd.DataFrame(data)
    # depois de criar o df com todas as colunas, inclusive publishedAt:
    df['publishedAt'] = pd.to_datetime(df['publishedAt'])
    df = df[
        (df['publishedAt'] >= '2024-01-01') &
        (df['publishedAt'] <  '2025-01-01')
    ]
    df.to_csv('f1_highlights_playlist.csv', index=False, encoding='utf-8-sig')
    print("✅ CSV gerado: f1_highlights_playlist.csv")

if __name__ == '__main__':
    main()
