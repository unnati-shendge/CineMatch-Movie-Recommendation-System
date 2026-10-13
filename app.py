import os
import streamlit as st
import requests
import sklearn
import nltk
import pandas as pd
import pickle
import joblib

st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide"
)

# Cinematic UI
st.markdown("""
<style>
.stApp {
    background: #101116;
    color: #F5F5F5;
}
.movie-title {
    font-size: 17px;
    font-weight: 700;
    margin-top: 10px;
    min-height: 48px;
}
.movie-info {
    color: #B9BBC6;
    font-size: 14px;
    line-height: 1.6;
}
.rating {
    color: #F5C518;
    font-weight: bold;
}
div.stButton > button {
    background-color: #F5C518;
    color: #101116;
    border: none;
    border-radius: 10px;
    font-weight: 700;
}
div.stButton > button:hover {
    background-color: #FFD84D;
    color: #101116;
}
div[data-baseweb="select"] > div {
    background-color: #252B38;
    border: 1px solid #454D5C;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


st.title("🎬 CineMatch")
st.caption("Discover your next favourite movie.")


with open("movies.pickle",'rb') as m:
    movies=pickle.load(m)

similarities=joblib.load("similarity.joblib")



@st.cache_data(ttl=86400)
def fetch_movie_details(movie_id):
    api_key = st.secrets["TMDB_API_KEY"] or os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    try:
        response = requests.get(
            url,
            params={"api_key": api_key,
                    "append_to_response": "credits,external_ids"
                    },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            directors=[
                person["name"]
                for person in data.get("credits",{}).get("crew",[])
                if person.get("job")=="Director"
            ]

            data["director_names"]=directors
            return data

    except requests.RequestException:
        pass

    return None


def recommend(movie):
    movie_index=movies[movies['title']==movie].index[0]

    recommendations=similarities[movie_index]

    movie_list=sorted(enumerate(recommendations),reverse=True,key=lambda x:x[1])[1:6]

    recommended_movies=[]
    
    for i in movie_list:
        movie_data = movies.iloc[i[0]]

        recommended_movies.append({
            "title": movie_data["title"],
            "id": movie_data["id"]
        })

    return recommended_movies


movie_names=movies['title'].values

name_movie=st.selectbox(
    "choose a movie you like",
    movie_names
    )




if st.button("✨ Find Similar Movies", use_container_width=True):
    st.write("Debug: Recommendation started")
    results=recommend(name_movie)
    st.write("Debug: Recommendation completed")
    st.subheader("### The Recommended Movies")

    cols=st.columns(5)

    for col, movie in zip(cols,results):
        with col:
            with st.container(border=True):
                details=fetch_movie_details(movie["id"])

                if not details:
                    st.write(f"**{movie['title'].title()}**")
                    st.caption("Details unavailable")
                    continue

                poster_path=details.get("poster_path")

                if poster_path:
                    poster_url = (
                        "https://image.tmdb.org/t/p/w500"
                        + poster_path
                        )
                    st.image(poster_url,use_container_width=True)
                else:
                    st.caption("Poster unavailable")


                title=details.get("title",movie["title"])
                st.markdown(
                    f'<div class="movie-title">{title}</div>',
                    unsafe_allow_html=True
                )

                release_date=details.get("release_date","")
                year=release_date[:4] if release_date else "Year Unknown"


                rating=details.get("vote_average")
                rating_text=(
                    f"{rating:.1f}/10"
                    if rating is not None and rating > 0
                    else "Not rated"
                )

                st.markdown(
                    f'<div class="movie-info">'
                    f'{year}<br>'
                    f'<span class="rating">★ {rating_text}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                directors=details.get("director_names",[])
                director_text=", ".join(directors) if directors else "unknown"

                st.caption(f"🎥 Director: {director_text}")


                overview=details.get("overview") or "No overview available"
                with st.expander("Movie overview:"):
                    st.write(overview)

                imdb_id=details.get("external_ids",{}).get("imdb_id")

                if imdb_id:
                    st.markdown(
                        f"[View on IMDb](https://www.imdb.com/title/{imdb_id}/)"
                    )



    

    