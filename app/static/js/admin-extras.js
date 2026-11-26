'use strict';
document.addEventListener('click',async event=>{
 const button=event.target.closest('[data-action]');if(!button)return;
 try{
  if(button.dataset.action==='membership'){
   const id=button.dataset.id;const items=await api('/admin/curricula/'+encodeURIComponent(id)+'/courses');
   openModal('Nhóm học phần của chương trình','Xác nhận môn thuộc chương trình và khóa học từ tài liệu nguồn.',`<form id="membership-form" data-id="${esc(id)}"><div class="field"><label for="membership-items">Danh sách học phần (JSON)</label><textarea id="membership-items" name="items" class="json-editor" required>${esc(JSON.stringify(items,null,2))}</textarea><small>Mỗi mục gồm course_id và group: elective (tự chọn) hoặc required (bắt buộc). Không trộn nguồn NEU và DEMO.</small></div><div class="field"><label for="membership-source">Tài liệu / bằng chứng nguồn</label><input id="membership-source" name="provenance" required maxlength="200" placeholder="URL chương trình, khóa và mục trong tài liệu"></div><div class="form-error"></div><div class="demo-callout">${icon('info')}Sau khi đổi nhóm môn, trạng thái xác minh được đặt lại. Chỉ xác nhận quy tắc 10/15 khi có đủ bằng chứng chính thức.</div></form>`,`<button class="btn btn-white" data-action="close">Hủy</button><button class="btn btn-primary" type="submit" form="membership-form">Lưu nhóm học phần</button>`,true);
  }else if(button.dataset.action==='syllabus-sync'){
   const course=state.adminRows.find(c=>c.id===button.dataset.id);
   openModal('Đồng bộ đề cương NEU',course.name,`<form id="syllabus-form" data-id="${esc(course.id)}"><div class="field"><label for="syllabus-id">ID đề cương đã xác minh</label><input id="syllabus-id" name="syllabus_id" value="${esc(course.syllabus_id||'')}" required maxlength="100" placeholder="Nhập ID thực tế từ API đề cương"><small>Mã môn không tự động được coi là ID đề cương.</small></div><div class="form-error"></div><div class="demo-callout">${icon('info')}Nội dung và kế hoạch giảng dạy được lưu nguyên bản từ NEU. Gợi ý kỹ năng phải được quản trị viên kiểm duyệt trước khi dùng.</div></form>`,`<button class="btn btn-white" data-action="close">Hủy</button><button class="btn btn-primary" type="submit" form="syllabus-form">Đồng bộ đề cương</button>`);
  }
 }catch(error){toast(error.message,true);}
});
document.addEventListener('submit',async event=>{
 const form=event.target;if(!['membership-form','syllabus-form'].includes(form.id))return;
 event.preventDefault();const data=Object.fromEntries(new FormData(form));const button=document.querySelector(`[form="${form.id}"]`);button.disabled=true;
 try{
  if(form.id==='membership-form'){
   let items;try{items=JSON.parse(data.items);}catch{throw new Error('JSON của danh sách học phần chưa hợp lệ.');}
   await api('/admin/curricula/'+encodeURIComponent(form.dataset.id)+'/courses',{method:'PUT',body:JSON.stringify({items,provenance:data.provenance})});
   closeModal();await adminView();toast('Đã lưu nhóm học phần. Cần xác nhận lại chương trình.');
  }else{
   const result=await api('/admin/syllabus/'+encodeURIComponent(form.dataset.id),{method:'POST',body:JSON.stringify(data)});
   openModal('Đã lưu nội dung đề cương','Dữ liệu nguyên bản và các gợi ý kỹ năng cần kiểm duyệt.',`<div class="field"><label>Nội dung từ API</label><textarea class="json-editor" readonly>${esc(JSON.stringify(result.raw,null,2))}</textarea></div><h3 class="subheading">Gợi ý liên kết kỹ năng</h3>${result.skill_proposals.map(p=>`<div class="path-line">${esc(p.skill_id)} · Bằng chứng: ${esc(p.evidence)} · Chưa kiểm duyệt</div>`).join('')||'<p style="font-size:10px;color:#a18bad">Chưa tìm thấy từ khóa kỹ năng trong nội dung.</p>'}`,`<button class="btn btn-primary" data-action="close">Đóng</button>`,true);
  }
 }catch(error){inlineError(error.message);}finally{if(button.isConnected)button.disabled=false;}
});
