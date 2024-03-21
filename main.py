from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import shutil
import asyncio
from git import Repo

app = FastAPI()


class GitRepo(BaseModel):
    git_url: str


@app.get("/")
async def get_main():
    return {"message": "Welcome to Code Reader!"}


@app.post("/get-repo-content/")
async def print_repo_url(repo: GitRepo):
    git_url = repo.git_url
    try:
        repo_name = git_url.split("/")[-1]
        repo_name = (
            repo_name.replace(".git", "") if repo_name.endswith(".git") else repo_name
        )

        temp_dir = f"./temp_{repo_name}"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        repo_dir = os.path.join(temp_dir, repo_name)
        print("start cloning")  # 開始克隆
        # 異步克隆倉庫
        await clone_repo_async(git_url, repo_dir)

        print("start reading")  # 開始讀取
        # 異步讀取所有文件
        content = await read_all_files_async(repo_dir)
        print("read finished. content length: ", len(content))  # 讀取完成。內容長度：
        # 確保在此處刪除臨時目錄
        shutil.rmtree(temp_dir)
        print("temp dir removed")  # 臨時目錄已刪除
        return {"content": content[:50000]}

    except Exception as e:
        # 如果出現異常，也應該清理臨時目錄
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=str(e))


async def clone_repo_async(git_url, repo_dir):
    loop = asyncio.get_event_loop()
    print(f"開始克隆倉庫: {git_url}")  # 開始克隆倉庫：
    await loop.run_in_executor(
        None, lambda: Repo.clone_from(git_url, repo_dir, depth=1)
    )
    print(f"倉庫克隆完成: {repo_dir}")  # 倉庫克隆完成：


async def read_all_files_async(directory):
    loop = asyncio.get_event_loop()
    print(f"開始讀取文件: {directory}")  # 開始讀取文件：
    content = await loop.run_in_executor(None, lambda: read_all_files(directory))
    print(f"文件讀取完成. 總字符數: {len(content)}")  # 文件讀取完成。總字符數：
    return content


def read_all_files(directory):
    all_text = ""
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        all_text += f"File: {file_name}\n\n" + file.read() + "\n\n"
                except UnicodeDecodeError:
                    print(f"無法以UTF-8編碼讀取文件: {file_path}")  # 無法以UTF-8編碼讀取文件：
                except Exception as e:
                    print(f"讀取文件時發生錯誤: {file_path}, 錯誤: {e}")  # 讀取文件時發生錯誤：
    return all_text

@app.get("/privacy-policy/", response_class=HTMLResponse)  # Define a new route for the Privacy Policy
async def get_privacy_policy():
    # Assuming the HTML file is in the root directory of your project
    file_path = "Privacy_Policy.html"
    if os.path.isfile(file_path):
        # Open and read the HTML file content
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        # Return the HTML content as an HTMLResponse
        return HTMLResponse(content=html_content)
    else:
        raise HTTPException(status_code=404, detail="Privacy Policy not found.")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=10000)
