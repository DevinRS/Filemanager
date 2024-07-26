from api import google_api
import streamlit as st
import pandas as pd
import os
from streamlit_pdf_viewer import pdf_viewer
import random

# region: -- CSS INJECTION --
# make the link color white and remove underline, open the link in the same tab
st.markdown(
    """
    <style>
    a {
        text-decoration: none;
        color: #FAFAFA !important;
    }
    a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# endregion

# region: -- SESSION STATES --

if "folder_name" not in st.session_state:
    st.session_state.folder_name = "Root"

if "folder_id" not in st.session_state:
    st.session_state.folder_id = google_api.PARENT_FOLDER_ID

if "files" not in st.session_state:
    st.session_state.files = google_api.list_files_in_folder(st.session_state.folder_id)

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = random.randint(0, 1000)

if "render_body" not in st.session_state:
    st.session_state.render_body = True

if "parent_folder" not in st.session_state:
    st.session_state.parent_folder = None

# endregion

# region: -- QUERY PARAMS --
if "fileid" and "filename" and "filetype" in st.query_params:
    fileid = st.query_params["fileid"]
    filename = st.query_params["filename"]
    filetype = st.query_params["filetype"]
    if filetype.startswith("image/"):
        google_api.download_file_from_folder(st.session_state.folder_id, fileid, filename)
        st.image(filename)
        os.remove(filename)
        st.session_state.render_body = False
    elif filetype == "application/pdf":
        google_api.download_file_from_folder(st.session_state.folder_id, fileid, filename)
        pdf_viewer(filename, height=1000)
        os.remove(filename)
        st.session_state.render_body = False
    elif filetype == "application/vnd.google-apps.folder":
        st.session_state.folder_id = fileid
        st.session_state.files = google_api.list_files_in_folder(fileid)
        st.session_state.render_body = True
        if st.session_state.folder_id != google_api.PARENT_FOLDER_ID:
            st.session_state.parent_folder = google_api.get_parent_folder(fileid)
            st.session_state.folder_name = filename
        else:
            st.session_state.parent_folder = None
            st.session_state.folder_name = "Root"
# endregion

if st.session_state.render_body:
    # region: -- PAGE BODY --
    st.title(f"📁 {st.session_state.folder_name}")
    folder_url = f"https://drive.google.com/drive/folders/{st.session_state.folder_id}"
    st.markdown(f"🌎 <a href='{folder_url}' target='_blank' class='button'>View in Google Drive</a>", unsafe_allow_html=True)
    if st.session_state.parent_folder:
        parent_folder_id = st.session_state.parent_folder
        parent_folder_name = google_api.get_folder_name(parent_folder_id)
        parent_folder_mime = "application/vnd.google-apps.folder"
        parent_folder_url = f"http://localhost:8501/?fileid={parent_folder_id}&filename={parent_folder_name}&filetype={parent_folder_mime}"
        st.markdown(f"⬆️ <a href='{parent_folder_url}' target='_self'>Go to previous folder</a>", unsafe_allow_html=True)

    # region: -- SEARCH BAR AND FILTER--
    # search bar to filter files based on name
    search = st.text_input("Search by Name", key="search")
    if search:
        st.session_state.files = google_api.filter_files_in_folder(st.session_state.folder_id, search)
    else:
        st.session_state.files = google_api.list_files_in_folder(st.session_state.folder_id)

    # radio button to filter files based on type
    file_types = ["All", "Folders", "Images", "PDFs"]
    file_type = st.radio("Filter by Type", file_types, key="file_type", horizontal=True)
    if file_type == "All":
        pass
    elif file_type == "Folders":
        st.session_state.files = [file for file in st.session_state.files if file["mimeType"] == "application/vnd.google-apps.folder"]
    elif file_type == "Images":
        st.session_state.files = [file for file in st.session_state.files if file["mimeType"].startswith("image/")]
    elif file_type == "PDFs":
        st.session_state.files = [file for file in st.session_state.files if file["mimeType"] == "application/pdf"]
    # endregion

    col1, col2, col3, col4 = st.columns([1, 12, 4, 8])
    col1.subheader(" ")
    col2.subheader("Name")
    col3.subheader("Size")
    col4.subheader("Last Modified")


    files = st.session_state.files
    for file in files:
        # region: -- FILE DISPLAY --
        fileid = file["id"]
        filename = file["name"]
        filetype = file["mimeType"]
        # create a checkbox with the key as the file id
        with col1:
            checkbox = st.checkbox(" ", key=fileid)
            if checkbox and file["id"] not in st.session_state.selected_files:
                st.session_state.selected_files.append(file["id"])
            elif not checkbox and file["id"] in st.session_state.selected_files:
                st.session_state.selected_files.remove(file["id"])
        url = f"http://localhost:8501/?fileid={fileid}&filename={filename}&filetype={filetype}"
        if file["mimeType"] == "application/vnd.google-apps.folder":
            col2.markdown(f"📁 <a href='{url}' target='_self'>{filename}</a>", unsafe_allow_html=True)
        # if the mimeType starts with "image/", then it is an image
        elif file["mimeType"].startswith("image/"):
            col2.markdown(f"📷 <a href='{url}' target='_blank'>{filename}</a>", unsafe_allow_html=True)
        # if the mimeType is "application/pdf", then it is a pdf
        elif file["mimeType"] == "application/pdf":
            col2.markdown(f"📄 <a href='{url}' target='_blank'>{filename}</a>", unsafe_allow_html=True)
        else:
            col2.markdown(f"<a href='{url}' target='_self'>{filename}</a>", unsafe_allow_html=True)
        if "size" in file:
            col3.write(file["size"])
        else:
            col3.write("N/A")
        col4.write(file["modifiedTime"])
        # endregion

    # endregion

    # region: -- SIDEBAR --
    st.sidebar.title(f"🐼 FileManager")
    # Magic Create popover
    magic_create = st.sidebar.popover("🪄 Magic Create", use_container_width=True)
    with magic_create:
        new_magic_folder_name = st.text_input("Folder Name", key="new_magic_folder_name")
        # radio button with the following options: [Class, Research, Student Organization, Work, Personal, Other]
        magic_folder_types = ["Class", "Research", "Student Organization", "Work", "Personal", "Other"]
        magic_folder_type = st.radio("Folder Type", magic_folder_types, key="magic_folder_type", horizontal=True)
        if magic_folder_type == "Class":
            magic_folder_subtypes = st.text_input("Subtypes (comma separated)", key="magic_folder_subtypes", value="Notes,Assignments,Projects,Exams", help="Default: Notes,Assignments,Projects,Exams")
        elif magic_folder_type == "Research":
            magic_folder_subtypes = st.text_input("Subtypes (comma separated)", key="magic_folder_subtypes", value="Data,Code,Papers,Experiments", help="Default: Data,Code,Papers,Experiments")
        elif magic_folder_type == "Student Organization":
            magic_folder_subtypes = st.text_input("Subtypes (comma separated)", key="magic_folder_subtypes", value="Events,Meetings,Projects,Members", help="Default: Events,Meetings,Projects,Members")
        elif magic_folder_type == "Work":
            magic_folder_subtypes = st.text_input("Subtypes (comma separated)", key="magic_folder_subtypes", value="Projects,Reports,Meetings,Invoices", help="Default: Projects,Reports,Meetings,Invoices")
        elif magic_folder_type == "Personal":
            magic_folder_subtypes = st.text_input("Subtypes (comma separated)", key="magic_folder_subtypes", value="Photos,Videos,Music,Documents", help="Default: Photos,Videos,Music,Documents")
        elif magic_folder_type == "Other":
            magic_folder_subtypes = st.text_input("Subtypes (comma separated)", key="magic_folder_subtypes", value="Subfolder1,Subfolder2,Subfolder3,Subfolder4", help="Default: Subfolder1,Subfolder2,Subfolder3,Subfolder4")
        if st.button("Create Magic Folder"):
            folder_id = google_api.create_folder_in_folder(st.session_state.folder_id, new_magic_folder_name)
            # Create subfolders based on the magic_folder_subtypes
            subtypes = magic_folder_subtypes.split(",")
            for subtype in subtypes:
                google_api.create_folder_in_folder(folder_id, subtype)
            st.session_state.files = google_api.list_files_in_folder(st.session_state.folder_id)
            st.rerun()
    # Create folder popover
    create_folder = st.sidebar.popover("New Folder", use_container_width=True)
    with create_folder:
        new_folder_name = st.text_input("Folder Name", key="new_folder_name")
        if st.button("Create"):
            google_api.create_folder_in_folder(st.session_state.folder_id, new_folder_name)
            st.session_state.files = google_api.list_files_in_folder(st.session_state.folder_id)
            st.rerun()
    # Delete folder popover
    delete_files = st.sidebar.popover("Delete Files", use_container_width=True)
    with delete_files:
        st.warning("⚠️ Deleting files is irreversible. Please proceed with caution.")
        item_count = len(st.session_state.selected_files)
        st.error(f"You selected {item_count} files for deletion.")
        if st.button("Delete"):
            # delete all selected files
            for file_id in st.session_state.selected_files:
                google_api.delete_folder(file_id)
            st.session_state.files = google_api.list_files_in_folder(st.session_state.folder_id)
            st.session_state.selected_files = []
            st.rerun()
    # Upload file popover
    upload_file = st.sidebar.popover("Upload File", use_container_width=True)
    with upload_file:
        file_name = st.text_input("File Name", key="file_name")
        uploaded_file = st.file_uploader("Choose a file", key=st.session_state.file_uploader_key)
        if st.button("Upload"):
            if uploaded_file and file_name:
                # Save file into a temporary location, upload it, and then delete it
                with open(file_name, "wb") as f:
                    f.write(uploaded_file.getvalue())
                google_api.upload_file_to_folder(st.session_state.folder_id, file_name, file_name)
                st.session_state.files = google_api.list_files_in_folder(st.session_state.folder_id)
                # delete the file after uploading
                os.remove(file_name)
                st.session_state.file_uploader_key = random.randint(0, 1000)
                st.rerun()
            else:
                st.warning("Please provide a file and a name.")
    # endregion
