- Các project là hoàn toàn riêng biệt, không có nhóm chat nao được sử dụng cho 2 project
- Nếu có > 1 project, cần bổ sung module thực hiện cấu hình group các nhóm chat vào project

Proect:

Trong project có nhiều tasks cần hoàn thành để thực hiện project, các task được tạo nên, cập nhật bởi các decision. Có tích hợp với user hierarchy

I. các thông tin của decision: các field xem decision log.xlsx


Search by:
- ID
- context
- description

Filter by:
- Time : start - end, filter weekly
- User

II. Các thông tin của Task : các field xem task log.xlsx
 

Search by:
- ID
- description

Filter by:
- Time : start - end, filter weekly
- PIC
- Team
- Status
- Type

Note:
- role base view: team member can only view his/her own tasks, teamlead can only view his team tasks … ( depends on organization)
- Một task có thể có nhiều PIC, phòng ban . PIC / phòng ban đều có thể null nếu chưa có người được chỉ định làm task

button reasoning:
- hiện pop-up sumarize lại các lý do, context của task và notes 
- kèm 1 decision log liên quan đến task, xắp xếp theo thứ tự thời gian, gần nhất => xa nhất .
- các field của decision log: Task_ID, description, user, time
- có option unhide superseded decisions
- cho phép back lại bản ghi task cũ khi click vào 1 decision log


III. các case cần chú ý

- Các decision phải được quyết định bởi người có đúng thẩm quyền ( giám đốc giao việc về các phòng, trưởng phòng giao việc về teamlead, teamlead giao cho nhân viên ...), cấp dưới không thể ảnh hưởng đến quyết định của người có cấp bậc cao hơn, nếu có đề xuât thì cần được duyệt bởi người có thẩm quyền mới có thể tạo bản ghi decision mới và cập nhật task, trừ việc PIC cập nhật tiến độ task )
- Các dự án đều có end date, nếu task không có end date, tự động set end date task = end date project - 1 day
- Cần có cảnh báo gửi về nếu task chưa có end date hoặc task giao với end date task > end date project
- PIC chỉ có thể chỉnh sửa các thông tin task của mình 
- Sau khi 1 task được update thủ công => bot nhắn tin vào nhóm, tag những người liên quan ( người ra quyết định, người được assign, người có task dependence , etc. )

IV. Open question
- Task dependency, cross-team dependency cần xử lý thế nào
- Surface potential blocker ( 1 người làm nhiều task cùng lúc, cần check tất cả các task của 1 người để biết người đó đang overload hay không để hiển thị warning cho người đó. tuy vậy task vẫn có thể được giao thêm bởi người có thẩm quyền ? Hoặc check progress như thế nào )