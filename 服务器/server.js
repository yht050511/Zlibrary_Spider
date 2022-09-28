// 提供服务器,让download.py下载
var express = require("express");
// var cors = require("cors");

var app = express();
// app.use(cors());

app.use('/temp',express.static("./temp"));

app.get("/api/info", function (req, res) {
  res.set("Content-Type", "text/plain; charset=utf-8");
  res.end(
    '{"equipmentType":"File Server","equipmentInfo":"文件存储服务器","serveType":["api"],"compose":"Haotian Yang"}'
  );
});

app.listen(8081, function () {
  console.log("Start");
});
