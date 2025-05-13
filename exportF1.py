import os
from dotenv import load_dotenv
import pandas as pd
from googleapiclient.discovery import build

# Carrega API_KEY de .env
load_dotenv()
API_KEY    = os.getenv('YOUTUBE_API_KEY')
CHANNEL_ID = 'UCB_qr75-ydFVKSF9Dmo6izg'

def get_highlight_video_ids(youtube, channel_id):
    ids, token = [], None
    while True:
        resp = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            q='highlight',
            type='video',
            #Garante que na puxada da API pegue só videos de janeiro de 2024 até dezembro de 2024
            publishedAfter='2024-01-01T00:00:00Z',
            publishedBefore='2025-01-01T00:00:00Z',  
            pageToken=token
        ).execute()
        ids += [i['id']['videoId'] for i in resp['items']]
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
    ids     = get_highlight_video_ids(youtube, CHANNEL_ID)
    data    = get_videos_details(youtube, ids)

    # Cria DataFrame
    dataset = pd.DataFrame(data)

    # Gera CSV
    output_file = 'f1_highlights_2024.csv'
    dataset.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ CSV gerado: {output_file}")

if __name__ == '__main__':
    main()
