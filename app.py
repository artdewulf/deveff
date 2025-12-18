import streamlit as st
import requests
import pandas as pd

# --- Helper Functions ---
def reconstruct_abstract(inverted_index):
    """Reconstructs the abstract text from OpenAlex's inverted index format."""
    if not inverted_index:
        return None
    max_index = 0
    for indices in inverted_index.values():
        max_index = max(max_index, max(indices))
    abstract_words = [""] * (max_index + 1)
    for word, indices in inverted_index.items():
        for index in indices:
            abstract_words[index] = word
    return " ".join(abstract_words)

# --- App Configuration ---
st.set_page_config(page_title="Development Effectiveness Search", page_icon="🌍")
st.title("🌍 Development Effectiveness & Aid Search")
st.markdown("Searching specifically within **International Development and Aid**.")

# --- Session State Initialization ---
if 'page' not in st.session_state:
    st.session_state['page'] = 1

# --- Input Section ---
selected_principle = st.radio(
    "Filter by Development Effectiveness Principle:",
    [
        "Country Ownership", 
        "Focus on Results", 
        "Inclusive Partnerships", 
        "Transparency and Accountability"
    ],
    horizontal=True
)

query = st.text_input("Enter keyword:", placeholder="e.g., Microfinance, cash transfers")

# --- Reset Logic ---
# If the user changes the query or filter, we must reset to Page 1.
# We store the last query/filter to detect changes.
current_search_hash = f"{query}_{selected_principle}"
if 'last_search_hash' not in st.session_state:
    st.session_state['last_search_hash'] = current_search_hash

if current_search_hash != st.session_state['last_search_hash']:
    st.session_state['page'] = 1
    st.session_state['last_search_hash'] = current_search_hash

# --- Search Logic ---
if query:
    # OpenAlex API Endpoint
    url = "https://api.openalex.org/works"
    
    combined_search = f"{query} AND \"{selected_principle}\""
    
    # 1. API Call for PAPERS (Uses Page Number)
    params_works = {
        "search": combined_search,
        "filter": "topics.id:T11168",
        "sort": "cited_by_count:desc",
        "per_page": 10,
        "page": st.session_state['page'], # <--- DYNAMIC PAGE NUMBER
        "mailto": "email@email.com"  
    }

    # 2. API Call for AUTHORS (Only needed on Page 1 usually, but we'll keep it)
    params_authors = {
        "search": combined_search,
        "filter": "topics.id:T11168",
        "group_by": "authorships.author.id",
        "mailto": "email@email.com"
    }

    st.caption(f"Searching for: `{combined_search}` | Page {st.session_state['page']}")

    with st.spinner("Fetching results..."):
        try:
            # --- Fetch Authors (Only show on Page 1 to reduce clutter?) ---
            # Let's keep it on all pages for now, or you can wrap in "if st.session_state['page'] == 1:"
            top_authors_data = []
            if st.session_state['page'] == 1:
                response_authors = requests.get(url, params=params_authors)
                if response_authors.status_code == 200:
                    author_groups = response_authors.json().get('group_by', [])
                    for group in author_groups[:10]:
                        top_authors_data.append({
                            "Author Name": group['key_display_name'],
                            "Works Count": group['count']
                        })

            # --- Fetch Papers ---
            response_works = requests.get(url, params=params_works)
            
            # --- UI RENDERING ---
            
            # A. Render Author Table (Only on Page 1)
            if top_authors_data:
                st.subheader("🏆 Top 10 Authors for this Query")
                df = pd.DataFrame(top_authors_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("---")

            # B. Render Papers
            if response_works.status_code == 200:
                data = response_works.json()
                results = data.get('results', [])
                total_count = data['meta']['count']
                
                if not results:
                    st.warning("No more results found.")
                else:
                    st.subheader(f"📚 Top Papers (Found {total_count})")
                    
                    for work in results:
                        # Extract Data
                        title = work.get('title') or "Untitled"
                        publication_year = work.get('publication_year')
                        cited_by = work.get('cited_by_count')
                        link = work.get('doi') or work.get('landing_page_url')
                        
                        authorships = work.get('authorships', [])
                        author_names = [a['author']['display_name'] for a in authorships]
                        if len(author_names) > 3:
                            author_str = ", ".join(author_names[:3]) + " et al."
                        else:
                            author_str = ", ".join(author_names)

                        # Display
                        with st.container():
                            if link:
                                st.markdown(f"### [{title}]({link})")
                            else:
                                st.markdown(f"### {title}")
                            
                            c1, c2, c3 = st.columns([2, 1, 1])
                            with c1: st.caption(f"✍️ {author_str}")
                            with c2: st.caption(f"📅 {publication_year}")
                            with c3: st.markdown(f"**⭐ Citations: {cited_by}**")
                            
                            abstract_text = reconstruct_abstract(work.get('abstract_inverted_index'))
                            if abstract_text:
                                st.markdown(f"<small>{abstract_text}</small>", unsafe_allow_html=True)
                            else:
                                st.caption("*No abstract available.*")
                            st.divider()

                    # --- PAGINATION BUTTONS ---
                    col_prev, col_next = st.columns([1, 1])
                    
                    with col_prev:
                        if st.session_state['page'] > 1:
                            if st.button("⬅️ Previous Page"):
                                st.session_state['page'] -= 1
                                st.rerun() # Force immediate reload

                    with col_next:
                        # Only show Next if there are more results to show
                        # (current_page * 10) < total_results
                        if (st.session_state['page'] * 10) < total_count:
                            if st.button("Next Page ➡️"):
                                st.session_state['page'] += 1
                                st.rerun() # Force immediate reload

            else:
                st.error(f"Error fetching works: {response_works.status_code}")

        except Exception as e:
            st.error(f"Connection failed: {e}")