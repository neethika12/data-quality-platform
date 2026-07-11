import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("📁 Data Explorer")
    st.write("Upload and explore your datasets")

    tab1, tab2 = st.tabs(["Upload Dataset", "Browse Datasets"])

    with tab1:
        st.subheader("Upload New Dataset")
        uploaded_file = st.file_uploader(
            "Choose a CSV or Parquet file",
            type=["csv", "parquet", "xlsx"]
        )

        if uploaded_file is not None:
            if st.button("Upload Dataset", use_container_width=True):
                with st.spinner("Uploading dataset..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file)}
                        response = requests.post(
                            f"{API_BASE_URL}/datasets/upload",
                            files=files,
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ Dataset uploaded successfully!")
                            st.json(result)
                        else:
                            st.error(f"Upload failed: {response.text}")

                    except Exception as e:
                        st.error(f"Error uploading: {e}")

    with tab2:
        st.subheader("Browse Datasets")

        try:
            response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
            if response.status_code == 200:
                datasets_data = response.json()
                datasets = datasets_data.get("datasets", [])

                if not datasets:
                    st.info("No datasets uploaded yet.")
                else:
                    # Create dataframe for display
                    df_display = pd.DataFrame([
                        {
                            "Name": d["name"],
                            "Rows": f"{d['row_count']:,}",
                            "Columns": d["column_count"],
                            "Created": d["created_at"][:10],
                            "Last Analyzed": d["last_analyzed"][:10] if d["last_analyzed"] else "Never"
                        }
                        for d in datasets
                    ])

                    st.dataframe(df_display, use_container_width=True)

                    # Select dataset for preview
                    st.divider()
                    st.subheader("Preview Dataset")

                    dataset_names = {d["id"]: d["name"] for d in datasets}
                    selected_id = st.selectbox(
                        "Select dataset to preview",
                        options=list(dataset_names.keys()),
                        format_func=lambda x: dataset_names[x]
                    )

                    if selected_id:
                        try:
                            response = requests.get(
                                f"{API_BASE_URL}/datasets/{selected_id}",
                                timeout=10
                            )
                            if response.status_code == 200:
                                dataset = response.json()
                                st.write(f"**Name**: {dataset['name']}")
                                st.write(f"**Rows**: {dataset['row_count']:,}")
                                st.write(f"**Columns**: {dataset['column_count']}")
                                st.write(f"**Columns**: {', '.join(dataset.get('columns', [])[:10])}")

                                if st.button("Delete Dataset", use_container_width=True):
                                    resp = requests.delete(
                                        f"{API_BASE_URL}/datasets/{selected_id}",
                                        timeout=10
                                    )
                                    if resp.status_code == 200:
                                        st.success("Dataset deleted")
                                        st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")

            else:
                st.error("Could not fetch datasets")

        except Exception as e:
            st.error(f"Error: {e}")
