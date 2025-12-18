import streamlit as st
import requests

# 1. App Layout & Title
st.set_page_config(page_title="OpenAlex Searcher", page_icon="📚")
st.title("📚 Scientific Literature Search")
st.markdown("Search millions of scientific papers using the [OpenAlex API](https://openalex.org).")

# 2. Input Section
query = st.text_input("Enter a topic, author, or keyword:", placeholder="e.g., Machine Learning, CRISPR")

# 3. Search Logic
if query:
    # OpenAlex API Endpoint for "Works" (Papers/Articles)
    url = "https://api.openalex.org/works"
    
    # Parameters: 
    # 'search': matches your query against titles, abstracts, etc.
    # 'per-page': limits results (default is 25)
    # 'mailto': Good etiquette! Identify yourself to get faster response rates.
    params = {
        "search": query,
        "per_page": 10, 
        "mailto": "example@email.com"  # <--- REPLACE THIS with your actual email
    }

    with st.spinner("Searching the global library..."):
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    st.warning("No results found.")
                else:
                    st.success(f"Found {data['meta']['count']} results. Showing top 10:")
                    
                    # 4. Display Results
                    for work in results:
                        # --- Data Extraction ---
                        title = work.get('title') or "Untitled"
                        publication_year = work.get('publication_year')
                        cited_by = work.get('cited_by_count')
                        
                        # Get URL (DOI is best, otherwise landing page)
                        doi = work.get('doi')
                        landing_page = work.get('landing_page_url')
                        link = doi if doi else landing_page
                        
                        # Extract Author Names (Authors are in a nested list)
                        authorships = work.get('authorships', [])
                        author_names = [a['author']['display_name'] for a in authorships]
                        # Join first 3 authors, add "et al." if more
                        if len(author_names) > 3:
                            author_str = ", ".join(author_names[:3]) + " et al."
                        else:
                            author_str = ", ".join(author_names)

                        # --- UI Layout for each result ---
                        with st.container():
                            # Header: Title (clickable)
                            if link:
                                st.markdown(f"### [{title}]({link})")
                            else:
                                st.markdown(f"### {title}")
                            
                            # Metadata row
                            c1, c2, c3 = st.columns([2, 1, 1])
                            with c1: st.caption(f"✍️ {author_str}")
                            with c2: st.caption(f"📅 {publication_year}")
                            with c3: st.caption(f"⭐ Cited by: {cited_by}")
                            
                            # Expandable Abstract (OpenAlex uses an 'inverted index' for abstracts)
                            # We keep it simple here. If you want abstracts, it requires reconstruction code.
                            # Instead, let's show the Journal/Source name if available.
                            if work.get('primary_location') and work['primary_location'].get('source'):
                                source_name = work['primary_location']['source']['display_name']
                                st.markdown(f"**Source:** *{source_name}*")
                                
                            st.divider() # Visual separator
                            
            else:
                st.error(f"Error {response.status_code}: {response.text}")
                
        except Exception as e:
            st.error(f"Connection failed: {e}")