import "https://cdn.datatables.net/2.0.3/js/dataTables.js"

const pyworker = await import((on_gae)?'./py-worker.min.js':'./py-worker.js');
const asyncRun = pyworker.asynRun;

const validate_metadata = await fetch(new URL('../python/bin/validation_metadata.py', import.meta.url, null)).then(response => response.text());
let dirHandle;


async function validateFile() {
    const fileInput = document.getElementById('myfile');
    const file = fileInput.files[0];

    if (file) {
        const spinner = document.getElementById('pgs_loading');
        spinner.style.visibility = "visible";

        const reader = new FileReader();
        reader.onload = async function(event) {
            const fileContent = new Uint8Array(event.target.result);
            let context = {
                file_content: fileContent,
                file_name: file.name,
                dirHandle: dirHandle
            }
            const { results, error } = await asyncRun(validate_metadata, context);
            if(results){
                console.log(results);
                spinner.style.visibility = "hidden";
                showResults(results);
            }
            if(error){
                console.error(error);
                spinner.style.visibility = "hidden";
                showSystemError(error);
            }
        };
        reader.readAsArrayBuffer(file);
    }
}

function report_items_2_html(reports_list) {
    let report = '<ul>';
    $.each(reports_list, function(index, report_item){
      let lines = ''
      if (report_item.lines) {
        let lines_label = (report_item.lines.length > 1) ? 'Lines' : 'Line';
        lines = lines_label+": "+report_item.lines.join(',')+ ' &rarr; ';
      }
      let message = report_item.message;
      // Value highlighting
      message = message.replace(/"(.+?)"/g, "\"<b>$1</b>\"");
      // Leading space
      message = message.replace(/"<b>\s+/g, "\"<b><span class=\"pgs_color_red\">_</span>");
      // Trailing space
      message = message.replace(/\s+<\/b>"/g, "<span class=\"pgs_color_red\">_</span></b>\"");
      // Column highlighting
      message = message.replace(/'(.+?)'/g, "\'<span class=\"pgs_color_1\">$1</span>\'");
      report += "<li>"+lines+message+"</li>";
    });
    report += '</ul>';
    return report;
}

function makeReportTable(data_spreadsheet_items, items_header){
    let table_html = '<table class="table table-bordered" style="width:auto"><thead class="thead-light">'+
                     '<tr><th>Spreadsheet</th><th>'+items_header+'</th></tr>'+
                     '</thead><tbody>';
        $.each(data_spreadsheet_items, function(spreadsheet, reports_list){
          table_html += "<tr><td><b>"+spreadsheet+"</b></td><td>";
          table_html += report_items_2_html(reports_list);
          table_html += '</td></tr>';
        });
        table_html += '</tbody></table>';
        return table_html;
}

function showResults(results){
    let data = JSON.parse(results);
    let status_style = (data.status === 'failed') ? '<i class="fa fa-times-circle pgs_color_red" style="font-size:18px"></i> Failed' : '<i class="fa fa-check-circle pgs_color_green" style="font-size:18px"></i> Passed';
    let status_html = '<table class="table table-bordered table_pgs_h mb-4"><tbody>'+
                        '  <tr><td>File validation</td><td>'+status_style+'</td></tr>'+
                        '</tbody></table>';
    $('#check_status').html(status_html);
    // Error messages
    if (data.error) {
        let report = '<h5 class="mt-4"><i class="fa fa-times-circle pgs_color_red"></i> Error report</h5>'
            + makeReportTable(data.error, 'Error message(s)');
        $('#report_error').html(report);
    } else {
        $('#report_error').html('');
    }
    // Warning messages
    if (data.warning) {
        let report = '<h5 class="mt-4"><i class="fa fa-exclamation-triangle pgs_color_amber"></i> Warning report</h5>'
            + makeReportTable(data.warning, 'Warning message(s)');
        $('#report_warning').html(report);
    } else {
        $('#report_warning').html('');
    }
}

function showSystemError(errors){
    let status_html = '<div><b>File validation:</b> <i class="fa fa-times-circle-o pgs_color_red"></i> Failed</div>';
      $('#check_status').html(status_html);
      let error_msg = (errors && errors !== '') ? errors : 'Internal error';
      let error_html = '<div class="clearfix">'+
                        '  <div class="mt-3 float_left pgs_note pgs_note_2">'+
                        '    <div><b>Error:</b> '+error_msg+'</div>'+
                        '  </div>'+
                        '</div>';
      $('#report_error').html(error_html);
}

document.querySelector('#upload_btn').addEventListener('click', async () => {
    await validateFile();
});
