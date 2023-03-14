var validation_service_url = 'https://validator-dot-pgs-catalog.appspot.com/validate';

$(document).ready(function() {
  var filename = $('#uploaded_filename').attr('data-value');
  console.log('filename: '+filename);
  if (filename) {
    console.log('validation_service_url: '+validation_service_url);
    $.ajax({
        url: validation_service_url,
        method: "POST",
        contentType: "application/json",
        dataType: 'json',
        data: JSON.stringify({"filename": filename})
    })
    .done(function (data) {
      console.log("SUCCESS");
      var status_style = (data.status == 'failed') ? '<i class="fa fa-times-circle pgs_color_red" style="font-size:18px"></i> Failed' : '<i class="fa fa-check-circle pgs_color_green" style="font-size:18px"></i> Passed';
      var status_html = '<table class="table table-bordered table_pgs_h mb-4"><tbody>'+
                        '  <tr><td>File validation</td><td>'+status_style+'</td></tr>'+
                        '</tbody></table>';
      $('#check_status').html(status_html);
      // Error messages
      if (data.error) {
        var report = '<h5 class="mt-4"><i class="fa fa-times-circle pgs_color_red"></i> Error report</h5>'+
                     '<table class="table table-bordered" style="width:auto"><thead class="thead-light">'+
                     '<tr><th>Spreadsheet</th><th>Error message(s)</th></tr>'+
                     '</thead><tbody>';
        $.each(data.error, function(spreadsheet, errors_list){
          report += "<tr><td><b>"+spreadsheet+"</b></td><td>";
          report += report_items_2_html(errors_list);
          report += '</td></tr>';
        });
        report += '</tbody></table>';
        $('#report_error').html(report);
      }
      else {
        $('#report_error').html('');
      }
      // Warning messages
      if (data.warning) {
        var report = '<h5 class="mt-4"><i class="fa fa-exclamation-triangle pgs_color_amber"></i> Warning report</h5>'+
                     '<table class="table table-bordered" style="width:auto"><thead class="thead-light">'+
                     '<tr><th>Spreadsheet</th><th>Warning message(s)</th></tr>'+
                     '</thead><tbody>';
        $.each(data.warning, function(spreadsheet, warnings_list){
          report += "<tr><td><b>"+spreadsheet+"</b></td><td>";
          report += report_items_2_html(warnings_list);
          report += '</td></tr>';
        });
        report += '</tbody></table>';
        $('#report_warning').html(report);
      }
      else {
        $('#report_warning').html('');
      }
    })
    .fail(function (xhRequest, ErrorText, thrownError) {
      var status_html = '<div><b>File validation:</b> <i class="fa fa-times-circle-o pgs_color_red"></i> Failed</div>';
      $('#check_status').html(status_html);
      error_msg = (thrownError && thrownError != '') ? thrownError : 'Internal error';
      var error_html = '<div class="clearfix">'+
                        '  <div class="mt-3 float_left pgs_note pgs_note_2">'+
                        '    <div><b>Error:</b> '+error_msg+'</div>'+
                        '  </div>'+
                        '</div>';
      $('#report_error').html(error_html);
    });
  }
  else {
    var error_html = '<div class="clearfix">'+
                      '  <div class="mt-3 float_left pgs_note pgs_note_2">'+
                      '    <div><b>Error:</b> The upload of the file "'+filename+'" failed.</div>'+
                      '  </div>'+
                      '</div>';
    $('#check_status').html('');
    $('#report_error').html(error_html);
  }


  // Display the reports in an HTML bullet point
  function report_items_2_html(reports_list) {
    var report = '<ul>';
    $.each(reports_list, function(index, report_item){
      var lines = ''
      if (report_item.lines) {
        var lines_label = (report_item.lines.length > 1) ? 'Lines' : 'Line';
        lines = lines_label+": "+report_item.lines.join(',')+ ' &rarr; ';
      }
      message = report_item.message;
      // Value highlighting
      message = message.replace(/\"(.+?)\"/g, "\"<b>$1</b>\"");
      // Leading space
      message = message.replace(/\"<b>\s+/g, "\"<b><span class=\"pgs_color_red\">_</span>");
      // Trailing space
      message = message.replace(/\s+<\/b>\"/g, "<span class=\"pgs_color_red\">_</span></b>\"");
      // Column highlighting
      message = message.replace(/\'(.+?)\'/g, "\'<span class=\"pgs_color_1\">$1</span>\'");
      report += "<li>"+lines+message+"</li>";
    });
    report += '</ul>';
    return report;
  }
});
