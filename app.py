import streamlit as st
import duckdb
from streamlit_searchbox import st_searchbox

st.set_page_config(layout="wide") 

atp_duck = duckdb.connect('atp.duckdb', read_only=True)

def search_players(search_term):
    query = '''
    SELECT DISTINCT winner_name AS player
    FROM matches
    WHERE player ilike '%' || $1 || '%'
    UNION
    SELECT DISTINCT loser_name AS player
    FROM matches
    WHERE player ilike '%' || $1 || '%'
    '''
    values = atp_duck.execute(query, parameters=[search_term]).fetchall()
    return [value[0] for value in values]

# def search_players(search_term):
#     query = '''
#     SELECT name_full
#     FROM players
#     WHERE name_full ilike '%' || $1 || '%'
#     '''
#     values = atp_duck.execute(query, parameters=[search_term]).fetchall()
#     return [value[0] for value in values]

st.title("ATP Head to Head")

left, right = st.columns(2)
with left:
    player1 = st_searchbox(search_players, label="Player 1", key="player1_search", default="Roger Federer", placeholder="Roger Federer")
with right:
    player2 = st_searchbox(search_players, label="Player 2", key="player2_search", default="Rafael Nadal", placeholder="Rafael Nadal")

st.markdown("***")

if player1 and player2:
    matches_for_players = atp_duck.execute("""
    SELECT tourney_date,tourney_name, surface, round, rounds.order AS roundOrder, levels.name AS level, levels.rank AS levelRank, winner_name, score
    FROM matches
    JOIN levels ON levels.short_name = matches.tourney_level
    JOIN rounds ON rounds.name = matches.round
    WHERE (loser_name  = $1 AND winner_name = $2) OR
          (loser_name  = $2 AND winner_name = $1)
    ORDER BY tourney_date DESC
    """, [player1, player2]).fetchdf()

    left, middle, right = st.columns(3)
    with left:
        st.markdown(f"<h2 style='text-align: left; '>{player1}</h1>", unsafe_allow_html=True)
    with right:
        st.markdown(f"<h2 style='text-align: right; '>{player2}</h1>", unsafe_allow_html=True)

    player1_wins = matches_for_players[matches_for_players.winner_name == player1].shape[0]
    player2_wins = matches_for_players[matches_for_players.winner_name == player2].shape[0]

    with middle:
        st.markdown(f"<h2 style='text-align: center; '>{player1_wins} vs {player2_wins}</h1>", unsafe_allow_html=True)

    # player1_profile = atp_duck.execute("""
    # SELECT *
    # FROM players
    # WHERE name_full = $1
    # """, [player1]).fetchdf()
    # st.write(player1_profile)

    # player2_profile = atp_duck.execute("""
    # SELECT *
    # FROM players
    # WHERE name_full = $1
    # """, [player2]).fetchdf()
    # st.write(player2_profile)

    # with left:
    #     st.markdown(f"""
    #         {player1_profile["hand"].values[0]}

    #         {player1_profile["ioc"].values[0]}

    #         {player1_profile["dob"].values[0]}
    #     """)
    #     st.write(player1_profile["hand"].values)
    #     st.write(player1_profile["dob"].values)

    # with right:
    #     st.markdown(f"""
    #         {player2_profile["hand"].values[0]}

    #         {player2_profile["ioc"].values[0]}
                        
    #         {player2_profile["dob"].values[0]}
    #     """)
    #     player2_profile["hand"].values

    if len(matches_for_players) == 0:
        pass
    else:        
        st.markdown(f'### Matches')
        st.dataframe(matches_for_players.drop(["roundOrder"], axis=1))

        # col1, col2, col3 = st.columns(3)
        st.markdown(f'### Match Breakdown')
        col1, col2, col3, col4 = st.tabs(["By Tournament", "By Surface", "By Tournament Level", "By Round"])

        with col1:
            st.markdown(f'#### By Tournament')
            by_tourn = atp_duck.sql("""
            PIVOT matches_for_players
            ON winner_name
            USING count(*)            
            GROUP BY tourney_name
            ORDER BY (#2 + #3) DESC
            """).fetchdf()
            st.dataframe(by_tourn)
        with col2:
            st.markdown(f'#### By Surface')
            by_surface = atp_duck.sql("""
            PIVOT matches_for_players
            ON winner_name
            USING count(*)
            GROUP BY surface
            ORDER BY (#2 + #3) DESC
            """).fetchdf()
            st.dataframe(by_surface)
        with col3:
            st.markdown(f'#### By Tournament Level')
            by_surface = atp_duck.sql("""
            WITH byLevel AS (
                PIVOT matches_for_players
                ON winner_name
                USING count(*)
                GROUP BY level, levelRank
                ORDER BY levelRank DESC
            )
            SELECT * EXCLUDE(levelRank)
            FROM byLevel            
            """).fetchdf()
            st.dataframe(by_surface)
        with col4:
            st.markdown(f'#### By Round')
            by_round = atp_duck.sql("""
            WITH byRound AS (
                PIVOT matches_for_players
                ON winner_name
                USING count(*)
                GROUP BY round, roundOrder
                ORDER BY roundOrder DESC
            ) 
            SELECT * EXCLUDE(roundOrder)
            FROM byRound
            """).fetchdf()
            st.dataframe(by_round)
