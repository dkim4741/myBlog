from main import *
from flask import Blueprint
from flask import send_from_directory

# routing using Blueprint
blueprint = Blueprint("board", __name__, url_prefix="/board")

def board_delete_attach_file(filename):
    abs_path = os.path.join(app.config["BOARD_ATTACH_FILE_PATH"], filename)
    if os.path.exists(abs_path):
        os.remove(abs_path)
        return True
    return False


@blueprint.route("/comment_list/<root_idx>", methods=["GET"])
@login_required
def comment_list(root_idx):
    if session["id"] is None or session["id"] == "":
        return redirect(url_for("member_login"))

    comment = mongo.db.comment
    comments = comment.find({"root_idx": str(root_idx)}).sort([("pubdate", -1)])

    comment_list = []
    for c in comments:
        print(c)
        owner = True if c.get("writer_id") == session.get("id") else False
        
        comment_list.append({
            "id": str(c.get("_id")),
            "root_idx": c.get("root_idx"),
            "name": c.get("name"),
            "writer_id": c.get("writer_id"),
            "comment": c.get("comment"),
            "pubdate": format_datetime(c.get("pubdate")),
            "owner": owner,
        })

    return jsonify(error="success", lists=comment_list)


@blueprint.route("/comment_write", methods=["POST"])
@login_required
def comment_write():
    if session["id"] is None or session["id"] == "":
        return redirect(url_for("member_login"))

    if request.method == "POST":
        name = session.get("name")
        writer_id = session.get("id")
        root_idx = request.form.get("root_idx")
        ccomment = request.form.get("comment")
        current_utc_time = round(datetime.utcnow().timestamp() * 1000)

        comment = mongo.db.comment

        post = {
            "root_idx": root_idx,
            "writer_id": writer_id,
            "name": name,
            "comment": ccomment,
            "pubdate": current_utc_time,
        }

        print(post)
        x = comment.insert_one(post)
        return redirect(url_for("board.board_view", idx=root_idx))
    return abort(404)


@blueprint.route("/comment_delete", methods=["POST"])
@login_required
def comment_delete():
    if session["id"] is None or session["id"] == "":
        return redirect(url_for("member_login"))

    if request.method == "POST":

        idx = request.form.get("id")
        comment = mongo.db.comment

        data = comment.find_one({"_id": ObjectId(idx)})
        if data.get("writer_id") == session.get("id"):
            comment.delete_one({"_id": ObjectId(idx)})
            return jsonify(error="success")
        else:
            return jsonify(error="error")
            
    return abort(404)


@blueprint.route("/comment_edit", methods=["POST"])
@login_required
def comment_edit():
    if session["id"] is None or session["id"] == "":
        return redirect(url_for("member_login"))

    if request.method == "POST":

        idx = request.form.get("id")
        ccomment = request.form.get("comment")

        comment = mongo.db.comment

        data = comment.find_one({"_id": ObjectId(idx)})
        if data.get("writer_id") == session.get("id"):
            comment.update_one(
                {"_id": ObjectId(idx)}, 
                {"$set": {"comment": ccomment}},
            )
            return jsonify(error="success")
        else:
            return jsonify(error="error")
            
    return abort(404)


@blueprint.route("/upload_image", methods=["POST"])
def upload_image():
    if request.method == "POST":
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = "{}.jpg".format(rand_generator())
            savefilepath = os.path.join(app.config["BOARD_IMAGE_PATH"], filename)
            file.save(savefilepath)
            return url_for("board.board_images", filename=filename)


@blueprint.route("/images/<filename>")
def board_images(filename):
    return send_from_directory(app.config["BOARD_IMAGE_PATH"], filename)


@blueprint.route("/files/<filename>")
def board_files(filename):
    return send_from_directory(app.config["BOARD_ATTACH_FILE_PATH"], filename, as_attachment=True)


@blueprint.route("/list")
def lists():
    # 페이지 값 (값이 없는 경우 기본값음 1)
    page = request.args.get("page", 1, type=int)

    # 한 페이지당 몇개의 게시물을 출력할지
    limit = request.args.get("limit", 7, type=int)

    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", "", type=str)

    # 최종적으로 완성된 쿼리를 만들 변수
    query = {}
    # 검색어 상태를 추가할 리스트 변수
    search_list = []

    if search == 0:
        search_list.append({"title": {"$regex": keyword}})
    elif search == 1:
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 2:
        search_list.append({"title": {"$regex": keyword}})
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 3:
        search_list.append({"name": {"$regex": keyword}})

    # 검색 대상이 한개라도 존재할 경우 query 변수에 $or 리스트를 쿼리 합니다.
    if len(search_list) > 0:
        query = {"$or": search_list}

    print(query)

    board = mongo.db.board
    datas = board.find(query).skip((page - 1) * limit).limit(limit).sort("pubdate", -1)
    result = []
    for data in datas:
        result.append(data)

    # 게시물의 총 갯수
    tot_count = board.count_documents(query)

    # 마지막 페이지의 수를 구합니다.
    last_page_num = math.ceil(tot_count / limit)
    # 페이지 블럭을 5개씩 표기
    block_size = 5
    # 현재 블럭의 위치
    block_num = int((page - 1) / block_size)
    # 블럭의 시작 위치
    block_start = int((block_size * block_num) + 1)
    # 블럭의 끝 위치
    block_last = math.ceil(block_start + (block_size - 1))

    return render_template(
        "list.html",
        datas=result,
        limit=limit,
        page=page,
        block_start=block_start,
        block_last=block_last,
        last_page_num=last_page_num,
        search=search,
        keyword=keyword,
        title="Board List"
        )


@blueprint.route("/view/<idx>")
@login_required
def board_view(idx):
    # idx = request.args.get("idx")
    if idx is not None:
        page = request.args.get("page")
        search = request.args.get("search")
        keyword = request.args.get("keyword")

        board = mongo.db.board
        # data = board.find_one({"_id": ObjectId(idx)})
        data = board.find_one_and_update({"_id": ObjectId(idx)}, {"$inc": {"view": 1}}, return_document=True)

        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "pubdate": data.get("pubdate"),
                "view": data.get("view"),
                "writer_id": data.get("writer_id", ""),
                "attachfile": data.get("attachfile", "")
            }
            return render_template("view.html", result=result, page=page, search=search, keyword=keyword, title="details")
    return abort(404)


@blueprint.route("/write", methods=["GET", "POST"])
@login_required
def board_write():
    # if session.get("id") is None:
    #    return redirect(url_for("member_login"))
    if request.method == "POST":
        filename = None
        if "attachfile" in request.files:
            file = request.files["attachfile"]
            if file and allowed_file(file.filename):
                filename = check_filename(file.filename)
                file.save(os.path.join(app.config['BOARD_ATTACH_FILE_PATH'], filename))

        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")

        request.files
        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.board
        post = {
            "name": name,
            "title": title,
            "contents": contents,
            "pubdate": current_utc_time,
            "writer_id": session.get("id"),
            "view": 0,
        }

        if filename is not None:
            post["attachfile"] = filename

        x = board.insert_one(post)
        print(x.inserted_id)
        return redirect(url_for("board.board_view", idx=x.inserted_id))

    else:
        return render_template("write.html", title="posting")


@blueprint.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    if request.method == "GET":
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("board.lists"))
        else:
            if session.get("id") == data.get("writer_id"):
                return render_template("edit.html", data=data, title="editing")
            else:
                flash("글 수정 권한이 없습니다.")
                return redirect(url_for("board.lists"))

    else:
        title = request.form.get("title")
        contents = request.form.get("contents")
        deleteoldfile = request.form.get("deleteoldfile", "")

        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if session.get("id") == data.get("writer_id"):
            attach_file = data.get("attachfile")
            filename = None
            if "attachfile" in request.files:
                file = request.files["attachfile"]
                if file and allowed_file(file.filename):
                    filename = check_filename(file.filename)
                    file.save(os.path.join(app.config["BOARD_ATTACH_FILE_PATH"], filename))
                    if attach_file:
                        board_delete_attach_file(attach_file)
            else:
                if deleteoldfile == "on":
                    filename = None
                    if attach_file:
                        board_delete_attach_file(attach_file)
                else:
                    filename = attach_file

            board.update_one({"_id": ObjectId(idx)}, {
                "$set": {
                    "title": title,
                    "contents": contents,
                    "attachfile": filename
                }
            })
            flash("수정되었습니다.")
            return redirect(url_for("board.board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("board.lists"))


@blueprint.route("/delete/<idx>")
def board_delete(idx):
    board = mongo.db.board
    data = board.find_one({"_id": ObjectId(idx)})
    if data.get("writer_id") == session.get("id"):
        board.delete_one({"_id": ObjectId(idx)})
        flash("삭제 되었습니다.")
    else:
        flash("삭제 권한이 없습니다.")
    return redirect(url_for("board.lists"))