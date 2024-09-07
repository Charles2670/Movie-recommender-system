import streamlit as st
import pickle
import pandas as pd
import requests


# Function to fetch movie poster and details from TMDB API
def fetch_movie_details(movie_id):
    api_key = "8265bd1679663a7ea12ac168da84d2e8"
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US")

    if response.status_code == 200:
        data = response.json()
        poster_url = "http://image.tmdb.org/t/p/w500/" + data.get('poster_path', '')
        overview = data.get('overview', 'No overview available.')
        release_date = data.get('release_date', 'Unknown release date.')
        rating = data.get('vote_average', 'N/A')
        runtime = data.get('runtime', 'N/A')
        genres = ", ".join([genre['name'] for genre in data.get('genres', [])])
        imdb_url = f"https://www.imdb.com/title/{data.get('imdb_id', '')}"

        return poster_url, overview, release_date, rating, runtime, genres, imdb_url
    else:
        return None, None, None, None, None, None, None


# Function to recommend movies based on similarity
def recommend(movie, sort_by='Similarity'):
    # Fetch index of the movie
    index = movies[movies['title'].str.lower() == movie.lower()].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movies = []
    recommended_movies_details = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id

        # Fetch movie details
        title = movies.iloc[i[0]].title
        poster_url, overview, release_date, rating, runtime, genres, imdb_url = fetch_movie_details(movie_id)

        recommended_movies.append(title)
        recommended_movies_details.append({
            'title': title,
            'poster_url': poster_url,
            'overview': overview,
            'release_date': release_date,
            'rating': rating,
            'runtime': runtime,
            'genres': genres,
            'imdb_url': imdb_url
        })

    # Optionally, sort by rating or other criteria
    if sort_by == 'Rating':
        recommended_movies_details.sort(key=lambda x: x['rating'], reverse=True)

    return recommended_movies, recommended_movies_details


# Load movie data and similarity matrix
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Streamlit UI components
st.set_page_config(page_title='Movie Recommender System', layout='wide')
st.title('Movie Recommender System')

# Search box for movies with auto-suggestions
selected_movie_name = st.selectbox("Search for a movie:", movies['title'].unique())

# Sort and filter options
sort_option = st.radio("Sort recommendations by:", ('Similarity', 'Rating'))
genre_filter = st.multiselect("Filter by Genre:",
                              ['Action', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Romance', 'Sci-Fi', 'Thriller'])
min_rating = st.slider("Minimum Rating:", 0.0, 10.0, 0.0, 0.5)

# Recommendations and Filtering
if st.button("Recommend"):
    with st.spinner('Fetching recommendations...'):
        if selected_movie_name.lower() in movies['title'].str.lower().values:
            names, movie_details = recommend(selected_movie_name, sort_by=sort_option)

            # Display recommendations with filters
            filtered_movies = [details for details in movie_details if
                               (not genre_filter or any(genre in details['genres'] for genre in genre_filter)) and (
                                           details['rating'] >= min_rating)]

            if filtered_movies:
                for i, details in enumerate(filtered_movies):
                    with st.expander(details['title']):
                        st.image(details['poster_url'] if details['poster_url'] else "Poster not available")
                        st.write(f"**Release Date:** {details['release_date']}")
                        st.write(f"**Rating:** {details['rating']}")
                        st.write(f"**Runtime:** {details['runtime']} minutes")
                        st.write(f"**Genres:** {details['genres']}")
                        st.write(f"**Overview:** {details['overview']}")
                        st.markdown(f"[More Info on IMDb]({details['imdb_url']})")
            else:
                st.write("No movies match your filters. Please adjust your criteria.")
        else:
            st.write("Please enter a valid movie name.")

