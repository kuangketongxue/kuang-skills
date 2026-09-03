---
name: qweather
description: 查询某地某时刻真实天气（和风天气 API）
---

# 和风天气查询

触发：用户问某地天气（"广州今天天气"、"北京明天下雨吗"、"上海下午几点最热"、"现在几点出门不下雨"等）。

## 1. 读凭证（DPAPI 加密，绝不写进 memory/日志/报告）

```bash
KEY=$(powershell.exe -NoProfile -Command "\$e=Get-Content 'C:\Users\kuang\.claude\.secrets\qweather_key.enc'; \$s=\$e|ConvertTo-SecureString; \$b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR(\$s); [Runtime.InteropServices.Marshal]::PtrToStringAuto(\$b)")
ID=$(powershell.exe -NoProfile -Command "\$e=Get-Content 'C:\Users\kuang\.claude\.secrets\qweather_id.enc'; \$s=\$e|ConvertTo-SecureString; \$b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR(\$s); [Runtime.InteropServices.Marshal]::PtrToStringAuto(\$b)")
```
key/ID 绝不复述、不进 memory/commit/对话。

## 2. 地名 → 经纬度

和风 Geo API：
```
curl -s "https://geoapi.qweather.com/v2/city/lookup?location=<地名URL编码>&adm=<可选>&key=$KEY&number=1"
```
取 `result[0].lon` + `lat`（如广州 113.32,23.13，北京 116.41,39.92）。
内置常用城市可直接用经纬度省一次调用。

## 3. 按需调 weather API

base = `https://p55xmdkfrf.re.qweatherapi.com`（用户私有域名，中国可访问，不需 VPN）
- 实时：`$base/v7/weather/now?location=<lon,lat>&key=$KEY`
- 3天预报：`$base/v7/weather/3d?location=<lon,lat>&key=$KEY`
- 24小时逐时：`$base/v7/weather/24h?location=<lon,lat>&key=$KEY`
- 分钟级降水（2小时）：`$base/v7/minutely/5m?location=<lon,lat>&key=$KEY`

## 4. 解析回答

- 某时刻天气：24h 接口 `hourly[].fxTime/temp/text/windSpeed`，按用户问的时刻找对应小时。
- 某日：3d 接口 `daily[].fxDate/tempMax/tempMin/textDay/textNight`。
- 实时：now 接口 `obsTime/temp/feelsLike/text/windScale/humidity`。
- 出门建议：结合降水（minutely/24h pop）、温度、风，给"几点出门不下雨/最舒服"。

## 注意
- 和风免费版 5万次/月，适度调用。
- key 绝不泄露（加密文件 + powershell 解密，不复述）。
- 中国可访问，不需 VPN。
