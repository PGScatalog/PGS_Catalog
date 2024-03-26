var rest_url = 'https://www.pgscatalog.org/rest/release/'

bg_colours = {
  'score': '#007C82',
  'publication': '#BE4A81',
  'performance': 'DodgerBlue',
  'trait': '#c03b23',
  'new_entry': '#FFC200'
};
bg_hover_colours = {
  'score': '#00adb5',
  'publication': '#e83e8c',
  'performance': '#51a9ff',
  'trait': '#f67d51',
  'new_entry': '#FFD700'
};

$('.get_pgs_ids').click(function() {
  id = $(this).attr('id');
  type = id.match(/^release_(\w+)_/)[1];
  if ($('#list_'+id).is(':empty')) {
    date = id.replace('release_'+type+'_','');
    $.ajax({
      url: rest_url+date,
      contentType: "application/json",
      dataType: 'json'
    })
    .done(function (result) {
        // Scores
        list_score_id = '#list_'+id.replace(type,'score');
        html_score = "<ul>";
        $.each(result.released_score_ids, function(index, pgs_id) {
          html_score += '<li><a href="/pgs/'+pgs_id+'/">'+pgs_id+'</a></li>';
        });
        html_score += '</ul>';
        $(list_score_id).html(html_score);

        list_pub_id = '#list_'+id.replace(type,'pub');
        html_pub = "<ul>";
        $.each(result.released_publication_ids, function(index, pgs_id) {
          html_pub += '<li><a href="/publication/'+pgs_id+'/">'+pgs_id+'</a></li>';
        });
        html_pub += '</ul>';
        $(list_pub_id).html(html_pub);
        $('#list_'+id).show();

        list_trait_id = '#list_'+id.replace(type,'trait');
        html_trait = "<ul>";
        $.each(result.released_new_trait_ids, function(index, trait_id) {
          html_trait += '<li><a href="/trait/'+trait_id+'/">'+trait_id+'</a></li>';
        });
        html_trait += '</ul>';
        $(list_trait_id).html(html_trait);
        $('#list_'+id).show();
    })
    .fail(function (xhRequest, ErrorText, thrownError) {
      console.log(xhRequest);
      console.log(ErrorText);
      console.log(thrownError);
    });
  }
});


// Build and draw sample distribution piecharts
function draw_js_barchart(data_chart, id, type) {
  var data_label = [];
  var data_new_value = [];
  var data_tot_value = [];

  var data_new_type = type+'_count'
  var data_tot_type = 'total_'+type+'_count'

  for(var i=0;i<data_chart.length;i++) {
    data_label.push(data_chart[i].date);
    data_new_value.push(data_chart[i][data_new_type]);
    data_tot_value.push(data_chart[i][data_tot_type]);
  }

  new Chart(document.getElementById(id), {
    type: 'bar',
    data: {
      labels: data_label,
      datasets: [
        {
          label: 'Previously released '+type+'s',
          data: data_tot_value,
          backgroundColor: bg_colours[type],
					hoverBackgroundColor: bg_hover_colours[type]
        },
        {
          label: 'New released '+type+'(s)',
          data: data_new_value,
					backgroundColor: bg_colours['new_entry'],
					hoverBackgroundColor: bg_hover_colours['new_entry']
        }
      ]
    },
    options: {
      title: {
        display: true,
        text: "Published PGS "+type+"s"
      },
      legend: {
        display: false
      },
      scales:{
        xAxes: {
          stacked: true
        },
        yAxes: {
          stacked: true
        }
      }
    }
  });
}


// Build and draw sample distribution piecharts
function draw_js_barchart_with_label(data_chart, id, title, type) {
  var data_label = [];
  var data_value = [];

  for(var i=0;i<data_chart.length;i++) {
    data_label.push(data_chart[i].year);
    data_value.push(data_chart[i].count);
  }

  var ctx = document.getElementById(id);
  new Chart(ctx, {
    type: 'bar',
    plugins: [ChartDataLabels],
    data: {
      labels: data_label,
      datasets: [
        {
          label: title,
          data: data_value,
          backgroundColor: bg_colours[type]
        }
      ]
    },
    options: {
      events: [], // Disable hover and tooltip
      title: {
        display: true,
        text: title
      },
      legend: {
        display: false
      },
      scales:{
        xAxes: {
          stacked: true
        },
        yAxes: {
          stacked: true
        }
      },
      responsive: false,
      plugins: {
        datalabels: {
          anchor: 'end', // remove this line to get label in middle of the bar
          align: 'end'
        }
      }
    }
  });
}


function draw_combined_js_barchart(data_chart, id) {
  var data_label = [];
  var data_score = [];
  var data_publication = [];
  var data_performance = [];

  // Scores
  s_type = 'score'
  var data_new_score = s_type+'_count'
  var data_tot_score = 'total_'+s_type+'_count'

  p_type = 'publication'
  var data_new_pub = p_type+'_count'
  var data_tot_pub = 'total_'+p_type+'_count'

  m_type = 'performance'
  var data_new_perf = m_type+'_count'
  var data_tot_perf = 'total_'+m_type+'_count'

  for(var i=0;i<data_chart.length;i++) {
    data_label.push(data_chart[i].date);
    data_score.push(data_chart[i][data_new_score]+data_chart[i][data_tot_score]);
    data_publication.push(data_chart[i][data_new_pub]+data_chart[i][data_tot_pub]);
    data_performance.push(data_chart[i][data_new_perf]+data_chart[i][data_tot_perf]);
  }

  var scoreData = {
    label: 'Published PGS Scores',
    data: data_score,
    backgroundColor: bg_colours['score'],
    hoverBackgroundColor: bg_hover_colours['score']
  };

  var publicationData = {
    label: 'Published PGS Publications',
    data: data_publication,
    backgroundColor: bg_colours['publication'],
    hoverBackgroundColor: bg_hover_colours['publication']
  };

  var performanceData = {
    label: 'Published PGS Performance Metrics',
    data: data_performance,
    backgroundColor: bg_colours[2],
    hoverBackgroundColor: bg_colours[3]
  };

  new Chart(document.getElementById(id), {
    type: 'bar',
    data: {
      labels: data_label,
      datasets: [ scoreData, publicationData ]
    },
    options: {
      title: {
        display: true,
        text: "Published PGS data"
      }
    }
  });
}


function draw_combined_js_linechart(data_chart, id) {
  var data_label = [];
  var data_score = [];
  var data_publication = [];
  var data_performance = [];

  // Scores
  s_type = 'score'
  var data_new_score = s_type+'_count'
  var data_tot_score = 'total_'+s_type+'_count'

  p_type = 'publication'
  var data_new_pub = p_type+'_count'
  var data_tot_pub = 'total_'+p_type+'_count'

  m_type = 'performance'
  var data_new_perf = m_type+'_count'
  var data_tot_perf = 'total_'+m_type+'_count'

  for(var i=0;i<data_chart.length;i++) {
    data_label.push(data_chart[i].date);
    data_score.push(data_chart[i][data_new_score]+data_chart[i][data_tot_score]);
    data_publication.push(data_chart[i][data_new_pub]+data_chart[i][data_tot_pub]);
    data_performance.push(data_chart[i][data_new_perf]+data_chart[i][data_tot_perf]);
  }

  var scoreData = {
    label: 'Published PGS Scores',
    data: data_score,
    borderColor: bg_colours['score'],
    hoverBorderColor: bg_hover_colours['score'],
    backgroundColor: 'rgba(0, 0, 0, 0)',
    cubicInterpolationMode: 'monotone'
  };

  var publicationData = {
    label: 'Published PGS Publications',
    data: data_publication,
    borderColor: bg_colours['publication'],
    hoverBorderColor: bg_hover_colours['publication'],
    backgroundColor: 'rgba(0, 0, 0, 0)',
    cubicInterpolationMode: 'monotone'
  };

  var performanceData = {
    label: 'Published PGS Performance Metrics',
    data: data_performance,
    borderColor: bg_colours[2],
    hoverBorderColor: bg_colours[3],
    backgroundColor: 'rgba(0, 0, 0, 0)',
    cubicInterpolationMode: 'monotone'
  };

  new Chart(document.getElementById(id), {
    type: 'line',
    data: {
      labels: data_label,
      datasets: [ scoreData, publicationData ]
    },
    options: {
      title: {
        display: true,
        text: "Published PGS data"
      },
      scales: {
        xAxes: {
          type: 'time',
          time: {
            parser: 'DD/MM/YY'
          }
        }
      }
    }
  });
}
