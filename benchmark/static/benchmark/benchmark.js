var svg_id = 'pgs_chart';
var sep = '__';
var file_name = 'PGS_benchmark';
// X axis label
var chart_xaxis_label = 'PGS Catalog - Score ID';
// Colours to differenciate the ancestries
var ancestry_colours = {
  'European'    : "#367DB7",
  'African'     : "#4CAE49",
  'South Asian' : "#974DA2"
};
var chart_colours = ["#FF7C43", "#E50000", "#FFA600"];
// Point symbols/shapes to differenciate the cohorts data
var chart_shapes = [ d3.symbolCircle, d3.symbolTriangle, d3.symbolDiamond, d3.symbolSquare, d3.symbolStar, d3.symbolCross];

var chart_shapes_html_prefix = 'pgs_benchmark_shape_';
var chart_shapes_html = [
  // First set with filled shapes
  'circle',   // Circle
  'triangle', // Triangle
  'diamond',  // Diamond
  'square',   // Square
  'star',     // Star
  'cross',    // Cross
  // Second set with same shapes but outlined (i.e stroke)
  'circle_o',   // Circle outline
  'triangle_o', // Triangle outline
  'diamond_o',  // Diamond outline
  'square_o',   // Square outline
  'star_o',     // Star outline
  'cross_o'     // Cross outline
];

chart_shapes_html = chart_shapes_html.map(function(element){
    return chart_shapes_html_prefix+element;
});

// Horizontal lines - threshold
var threshold = { 'Hazard Ratio': 1, 'Odds Ratio': 1, 'C-index': 0.5, 'AUROC': 0.5, 'DeltaC': 0, 'DeltaAUROC': 0, 'Delta-C-index': 0};
// Font family
var font_family = '"Verdana", "Arial", "sans-serif"';
// Min width
var min_svg_width = 750;
// Max width
var max_svg_width = 1200;
// Min height
var min_svg_height = 400;//450;
// Max height
var max_svg_height = 500;
// Threshold of Categories (Polygenic Score IDs) to rotate the horizontal X axis labels
var max_x_horizontal_labels = 14;
// Threshold to display all the vertical lines with the default size
var max_line_display_full_size = 60;
// Default size of the data point
var default_point_size = 60;
// Y axis title - horizontal position
var y_label_y = 5;
// Top list filter value
var top_list_value = $(".benchmark_sorting_filter_top").val();
if (!top_list_value) {
  top_list_value = 10;
}

var scores_table_id = '#bm_scores_table';


/*
 * Main class to build the 'PGS Benchmark' chart
 */
class PGSBenchmark {

  constructor(chart_data,width,height) {

    this.point_size = default_point_size;
    this.size_ratio = max_svg_width / max_svg_height;

    this.set_svg_size(width,height);

    // SVG space
    this.svg = d3.select('svg')
      .attr('width', this.width)
      .attr('height', this.height);

    this.margin = {top: 20, right: 200, bottom: 70, left: 70};
    this.set_chartWidthHeight();
    this.g = this.svg.append('g').attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');

    this.chartData = chart_data;

    this.cohortsList = set_cohortsList();

    this.cohorts = set_cohorts_selection();
    this.set_cohort_data_shapes();

    this.exportJSON_button();
    this.exportCSV_button();

    // Fetch the selected performance metric
    this.set_metric();
    // Fetch the selected sex type
    this.set_sex_type();
    // Fetch the selected data ordering
    this.set_data_ordering();

    // Get the data corresponding to the filters selection
    this.set_selected_data();

    // Groups (ancestries)
    this.ancestryNames = set_ancestryNames();
    this.set_ancestryNames_colours();

    // Reset X axis categories (score IDs list) and sort them
    this.set_data_sorting();

    // X axis groups (ancestries)
    this.set_cohortAncestryNames();
    this.set_cohortAncestryNames_colours();

    // Define the div for the tooltip
    var div = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    // Draw chart
    this.draw_chart();
  }


  // Draw the different components of the chart
  draw_chart() {
    /* Setup scaling */

    // Setup the min/max for the Y scale
    this.get_min_max_values();

    // (Re)set the axes and scales
    this.set_all_axes();

    /* Drawing/updating chart */

    // Draw Axes
    this.addAxes();
    // Draw threshold/horizontal line
    this.addHorizontalLine()
    // Load data in the chart
    this.addData();
    // Load legend in the chart
    this.addLegend();
  }

  // Redraw chart when the browser window is resized
  redraw_chart() {

    var stored_with = this.width;
    var current_width = ($('div.container-fluid').width());

    if (current_width!=stored_with) {
      /* Set the new SVG width & height */
      this.set_svg_size();
      this.set_chartWidthHeight();

      /* Reset chart container */
      // Remove "old" chart
      d3.select('svg').remove();

      this.svg =  d3.select('#'+svg_id+'_container').append('svg')
                    .attr('id', svg_id)
                    .attr('height', this.height)
                    .attr('width', this.width);
      this.g = this.svg.append('g').attr('transform', 'translate(' + this.margin.left + ',' + this.margin.top + ')');

      /* Redraw chart */
      this.draw_chart();
    }
  }


  /* Draw the chart axes */
  // X Axis
  addXAxis() {
    // X axis - bar
    var x_axis = this.g.append('g')
      .attr("class", "xaxis")
      .attr('transform', 'translate(0,' + this.chartHeight + ')')
      .call( d3.axisBottom(this.x0))
      .attr("font-family", font_family);

    var x_label_margin = 25;

    if (this.pgsList.length > max_x_horizontal_labels || this.width==min_svg_width) {
      x_axis.selectAll("text")
        .style("text-anchor", "end")
        .attr("font-family", font_family)
        .attr("dx", "-.7em")
        .attr("dy", ".15em")
        .attr("transform", "rotate(-40)");

      x_label_margin = 6;
    }

    // X axis - label
    this.svg.selectAll('.x_label').remove();
    this.svg.append("text")
        .attr("class", "x_label")
        .attr("font-family", font_family)
        .attr("transform", "translate(" + (this.chartWidth/2) + " ," + (this.height - x_label_margin) + ")")
        .style("text-anchor", "middle")
        .text(chart_xaxis_label);
  }
  // Y Axis
  addYAxis() {
    // Y axis - bar
    this.g.append('g')
      .attr("class", "yaxis")
      .call( d3.axisLeft(this.y) )
      .attr("font-family", font_family);
    // Y axis - label
    this.svg.append("text")
      .attr("class", "y_label")
      .attr("font-family", font_family)
      .attr("transform", "rotate(-90)")
      .attr("y", y_label_y)
      .attr("x", 0 - (this.height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .text(this.metric);
  }
  // X & Y Axes
  addAxes() {
    this.addXAxis();
    this.addYAxis();
  }


  // Draw the horizontal line (threshold)
  addHorizontalLine() {
    var y_val = 0;
    if (threshold[this.metric]) {
      y_val = threshold[this.metric];
    }

    if (y_val > this.min_value && y_val < this.max_value) {
      var y_coord = this.y(y_val)
      this.g.append("line")
        .attr("class", "chart_hline")
        .attr("stroke", 'black')
        .attr("stroke-width", 1)
        .style("stroke-dasharray", ("6, 6"))
        .attr('x1', 0)
        .attr('x2', this.chartWidth)
        .attr('y1', y_coord)
        .attr('y2', y_coord);
    }
  }


  // Draw the chart content
  addData() {
    // Chart container
    var chart_content = this.g.append("g").attr('class', 'chart_content');

    // Use a different variable name to avoid issue within the d3 functions
    var obj = this;

    // Cohorts
    var global_selected_data = [];
    var cohorts = Object.keys(this.selected_data);
    for (var i=0;i<cohorts.length;i++) {
      var cohort = cohorts[i];
      for (var j=0;j<this.selected_data[cohort].length;j++) {
        if (this.ancestryNames.indexOf(this.selected_data[cohort][j].anc) != -1 && this.pgsList.indexOf(this.selected_data[cohort][j].pgs)  != -1) {
          var entry = this.selected_data[cohort][j];
          entry['cohortAncestry'] = cohort+sep+entry.anc;
          global_selected_data.push(entry);
        }
      }
    }

    var s_width = 2;
    var l_span = 5;
    this.point_size = 60;
    if (global_selected_data.length > max_line_display_full_size) {
      s_width = 1;
      l_span = 3;
      this.point_size = 30;
    }
    else {
      this.point_size = default_point_size;
    }

    /* Lines */
    var lines = chart_content.selectAll('line.error')
      .data(global_selected_data);

    // Vertical line
    lines.enter().filter(function(d){ return d.et; }).append('line')
      .attr('class', 'error')
      .attr('class', function(d) { return 'error '+d.anc })
      .attr("stroke", function(d) { return obj.z(d.cohortAncestry); })
      .attr("stroke-width", s_width)
    //.merge(lines)
      .attr('x1', function(d) { return obj.x1(d.cohortAncestry); })
      .attr('x2', function(d) { return obj.x1(d.cohortAncestry); })
      .attr('y1', function(d) { return obj.y(d.et); })
      .attr('y2', function(d) { return obj.y(d.eb); });
    // Horizontal line - top
    lines.enter().filter(function(d){ return d.et; }).append('line')
      .attr('class', function(d) { return 'error '+d.anc })
      .attr("stroke", function(d) { return obj.z(d.cohortAncestry); })
      .attr("stroke-width", s_width)
    //.merge(lines)
      .attr('x1', function(d) { return obj.x1(d.cohortAncestry)-l_span; })
      .attr('x2', function(d) { return obj.x1(d.cohortAncestry)+l_span; })
      .attr('y1', function(d) { return obj.y(d.et); })
      .attr('y2', function(d) { return obj.y(d.et); });
    // Horizontal line - bottom
    lines.enter().filter(function(d){ return d.et; }).append('line')
      .attr('class', function(d) { return 'error '+d.anc })
      .attr("stroke", function(d) { return obj.z(d.cohortAncestry); })
      .attr("stroke-width", s_width)
    //.merge(lines)
      .attr('x1', function(d) { return obj.x1(d.cohortAncestry)-l_span; })
      .attr('x2', function(d) { return obj.x1(d.cohortAncestry)+l_span; })
      .attr('y1', function(d) { return obj.y(d.eb); })
      .attr('y2', function(d) { return obj.y(d.eb); });

    chart_content.selectAll('line.error')
      //.transition()
      .attr("transform",function(d) { return "translate(" + obj.x0(d.pgs) + ",0)"; });


    /* Data points */
    for (var i=0;i<cohorts.length;i++) {
      var cohort = cohorts[i];
      var selected_data = [];

      for (var j=0;j<this.selected_data[cohort].length;j++) {
        if (this.ancestryNames.indexOf(this.selected_data[cohort][j].anc) != -1 && this.pgsList.indexOf(this.selected_data[cohort][j].pgs)  != -1) {
          selected_data.push(this.selected_data[cohort][j]);
        }
      }

      // Data points - each cohort has its point shape
      var points = chart_content.selectAll('data.point')
        .data(selected_data);
      points.enter()
        .append('path')
        .attr("transform",function(d) { return "translate(" + (obj.x0(d.pgs) + obj.x1(cohort+sep+d.anc)) +","+ obj.y(d.y)+")"; })
        //.attr("fill", function(d) { return obj.z(cohort+sep+d.anc); })
        .attr("fill", function(d) {
          if (obj.cohort_data_shapes[cohort]['type'] == 'fill') {
            return obj.z(cohort+sep+d.anc);
          }
          else {
            return 'white';
          }
        })
        .attr("stroke", function(d) {
          if (obj.cohort_data_shapes[cohort]['type'] == 'fill') {
            return 'None';
          }
          else {
            return obj.z(cohort+sep+d.anc);
          }
        })
        .attr('d', obj.get_point_path(obj.cohort_data_shapes[cohort]['shape']));
    }


    /* Rectangle area used by tooltip */
    chart_content.selectAll('rect')
      .data(global_selected_data)
      .enter()
      .append('rect')
      .attr('class', function(d) { return 'rect tooltip_area' })
      .attr("transform",function(d) { return "translate(" + obj.x0(d.pgs) + ",0)"; })
      .each(function(d,i){
        obj.addTooltip($(this), d);
      })
      .attr("x", function(d) {
        var span = (d.et) ? 6 : 3;
        return obj.x1(d.cohortAncestry) - span;
      })
      .attr("y", function(d) { return (d.et) ? obj.y(d.et) - 1 : obj.y(d.y) - 3 })
      .attr("width", function(d) { return (d.et) ? 12 : 10; })
      .attr("height", function(d) { return (d.et) ? obj.y(d.eb) - obj.y(d.et) + 2 : 10; })
      .attr("fill", "transparent");

      this.has_lines = ("eb" in global_selected_data[0]) ? true : false;
  }


  // Draw the legend
  addLegend() {
    var obj = this;

    var text_x = 30;

    var legend = this.g.append("g")
      .attr("font-family", font_family)
      .attr("font-size", 10)
      .attr("text-anchor", "start")
      .attr("class", "chart_legend")
      .selectAll("g")
      .data(this.cohortAncestryNames.slice())
      .enter().append("g")
      .attr("class", function(d) { return d; } )
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

    // Legend point with its corresponding shape
    legend.append('path')
      .attr("transform", function(d, i) { return "translate(" + (obj.chartWidth + 20) +",9.5)"; })
      .attr("fill", function(d) {
        if (obj.cohortAncestryNames_data_shapes[d]['type'] == 'fill') {
          return obj.z(d);
        }
        else {
          return 'white';
        }
      })
      .attr("stroke", function(d) {
        if (obj.cohortAncestryNames_data_shapes[d]['type'] == 'fill') {
          return 'None';
        }
        else {
          return obj.z(d);
        }
      })
      .attr('d', obj.get_point_path(function(d) { return obj.cohortAncestryNames_data_shapes[d]['shape']; }));

    legend.append("text")
      .attr("x", this.chartWidth + text_x)
      .attr("y", 9.5)
      .attr("dy", "0.32em")
      .attr("text-anchor", "start")
      .text(function(d) {
        var text = d.split(sep);
        return text[1]+" ("+text[0]+")";
      });
  }

  // Ser SVG dimension (width & height)
  set_svg_size(width,height) {
    if (!width || !height) {
      var tmp_width = ($('div.container-fluid').width());
      width = tmp_width;
      height = tmp_width / this.size_ratio;
    }

    if (width < min_svg_width || height < min_svg_height) {
      width = min_svg_width;
      height = min_svg_height;
    }
    else if (width > max_svg_width || height > max_svg_height) {
      width = max_svg_width;
      height = max_svg_height;
    }
    this.width = width;
    this.height = height;
    console.log("width: "+width+" | height: "+height);
  }

  // Set chart content width and height
  set_chartWidthHeight() {
    this.chartWidth = this.width - this.margin.left - this.margin.right,
    this.chartHeight = this.height - this.margin.top - this.margin.bottom;
  }

  // Set the x0, x1, y and z axes (scale)
  set_all_axes() {
    this.set_x0_axis();
    // The scale for spacing each group's bar:
    this.set_x1_axis();
    // The scale of the Y axis:
    this.set_y_axis(1);
    // The scale of the group/cohort colouring
    this.set_z_axis();
  }

  // Set axis scales
  set_x0_axis() {
    var obj = this;
    obj.x0 = d3.scaleBand()
      .domain(obj.pgsList)
      .rangeRound([0, obj.chartWidth])
      .paddingInner(0.05);
    // Show hide table rows depending on the selection
    if (!obj.score_data) {
      setTimeout(function () {
        obj.score_data = $(scores_table_id).bootstrapTable('getData');
        obj.show_hide_table_rows();
      }, 100);
    }
    else {
      obj.show_hide_table_rows();
    }
  }
  set_x1_axis() {
    this.x1 = d3.scaleBand()
      .domain(this.cohortAncestryNames)
      .rangeRound([0, this.x0.bandwidth()])
      .padding(1);
  }
  set_y_axis(use_transition) {
    this.y = d3.scaleLinear()
      .domain([this.min_value, this.max_value])
      .rangeRound([this.chartHeight, 0]);

    if (use_transition) {
      this.svg.select(".yaxis")
        .transition().duration(800)
        .call( d3.axisLeft(this.y) );
    }
  }
  set_z_axis() {
    this.z = d3.scaleOrdinal()
      .domain(this.cohortAncestryNames)
      .range(this.get_cohortAncestryNames_colours());
  }

  // Show hide table rows depending on the selections
  show_hide_table_rows() {
    var obj = this;
    var pgs_ids_list = [];
    $.each(obj.score_data,function(i, row) {
      var pgs_td = row['id'];
      var pgs_id = $(pgs_td).text().split('(')[0].trim();
      if (obj.pgsList.includes(pgs_id)) {
        pgs_ids_list.push(pgs_td);
      }
    });
    $(scores_table_id).bootstrapTable('filterBy', {
      id: pgs_ids_list
    });
  }

  // Get the cohort-ancestrys
  set_cohortAncestryNames() {
    var cohort_gp_list = [];
    var cohorts = Object.keys(this.selected_data);

    if (this.data_ordering=='cohort') {
      for (var i=0;i<cohorts.length;i++) {
        var cohort = cohorts[i];
        var ancestry_list = this.chartData.ancestries[cohort];
        // Ancestries
        for (var j=0; j<ancestry_list.length;j++) {
          var ancestry = ancestry_list[j];
          if (this.ancestryNames.includes(ancestry)) {
            cohort_gp_list.push(cohort+sep+ancestry);
          }
        }
      }
    }
    else if (this.data_ordering=='ancestry') {
      for (var i=0;i<this.ancestryNames.length; i++) {
        var groupName=this.ancestryNames[i];
        for (var j=0;j<cohorts.length;j++) {
          var cohort = cohorts[j];
          var ancestry_list = this.chartData.ancestries[cohort];
          if (ancestry_list.includes(groupName)) {
            cohort_gp_list.push(cohort+sep+groupName);
          }
        }
      }
    }

    this.cohortAncestryNames = cohort_gp_list;
    this.set_cohortAncestryNames_data_shapes();
  }


  /* Assign data point shapes ('path' in D3) */

  // Get D3 data point path
  get_point_path(symbol){
    return d3.symbol().type(symbol).size(this.point_size);
  }
  // Define a data point shape for each cohort
  set_cohort_data_shapes() {
    this.cohort_data_shapes = {};
    this.cohort_data_shapes_html = {};
    var shapes_length = chart_shapes.length;
    for (var i=0; i<this.cohorts.length; i++) {
      var shape = '';
      var shape_type = 'fill';
      if (i >= shapes_length) {
        shape = chart_shapes[i - shapes_length];
        shape_type = 'stroke';
      }
      else {
        shape = chart_shapes[i];
      }
      this.cohort_data_shapes[this.cohorts[i]] = {'shape': shape, 'type': shape_type };
      this.cohort_data_shapes_html[this.cohorts[i]] = chart_shapes_html[i];
    }
  }
  // Define a data point shape for each cohort-ancestry (ancestry)
  set_cohortAncestryNames_data_shapes() {
    this.cohortAncestryNames_data_shapes = {};
    this.cohortAncestryNames_data_shapes_test = {};
    for (var i=0; i<this.cohortAncestryNames.length; i++) {
      var cohortGroupName = this.cohortAncestryNames[i]
      var cohort = cohortGroupName.split(sep)[0];
      this.cohortAncestryNames_data_shapes[cohortGroupName] = this.cohort_data_shapes[cohort];
      this.cohortAncestryNames_data_shapes_test[cohortGroupName] = this.cohort_data_shapes[cohort]['shape'];
    }
  }


  /* Assign the group/ancestry colours */

  // Set the group colours
  set_ancestryNames_colours() {
    var gp_colours = {};
    var extra_colour = 0
    for (var i=0; i<this.chartData.ancestry_groups.length; i++) {
      var gp_name = this.chartData.ancestry_groups[i];
      var colour = '';
      if (ancestry_colours[gp_name]) {
        colour = ancestry_colours[gp_name];
      }
      else {
        colour = chart_colours[extra_colour];
        extra_colour++;
      }
      gp_colours[gp_name] = colour;
    }
    this.ancestryNames_colours = gp_colours;
  }
  // Set the cohort-ancestry colours
  set_cohortAncestryNames_colours() {
    this.cohortAncestryNames_colours = {};
    var gp_colours = {};
    for (var i=0; i<this.cohortsList.length; i++) {
      var cohort = this.cohortsList[i];
      var ancestry_list = this.chartData.ancestries[cohort];
      // Ancestries
      for (var j=0; j<ancestry_list.length;j++) {
        var ancestry = ancestry_list[j];
        var cohort_gp_name = cohort+sep+ancestry;
        this.cohortAncestryNames_colours[cohort_gp_name] = this.ancestryNames_colours[ancestry];
      }
    }
  }
  // Get the cohort-ancestry colours
  get_cohortAncestryNames_colours() {
    var gp_colours = [];
    for (var i=0; i<this.cohortAncestryNames.length; i++) {
      var gp_name = this.cohortAncestryNames[i];
      gp_colours.push(this.cohortAncestryNames_colours[gp_name]);
    }
    return gp_colours;
  }


  // Fetch the data of the selected cohorts
  set_selected_data(param) {
    var available_cohorts = [];
    // Get available cohorts for the selected metric and sex
    for (var i=0; i<this.cohortsList.length; i++) {
      var cohort = this.cohortsList[i];
      var metrics = Object.keys(this.chartData["data"][cohort]);
      if (metrics.includes(this.metric)) {
        var sexes = Object.keys(this.chartData["data"][cohort][this.metric]);
        if (sexes.includes(this.sex_type)) {
          available_cohorts.push(cohort);
        }
      }
    }

    // Get data selection for the selected cohort, metric and sex
    this.selected_data = {};
    for (var i=0; i<this.cohorts.length; i++) {
      var cohort = this.cohorts[i];
      var metrics = Object.keys(this.chartData["data"][cohort]);
      if (metrics.includes(this.metric)) {
        var sexes = Object.keys(this.chartData["data"][cohort][this.metric]);
        if (sexes.includes(this.sex_type)) {
          var data = this.chartData["data"][cohort][this.metric][this.sex_type];
          this.selected_data[cohort] = data;
        }
      }
    }

    /* Alter forms selection, depending on the selected dataset(s) */
    var available_ancestryNames = [];
    var obj = this;
    var cohorts_selection = Object.keys(this.selected_data);
    // Show/Hide "Cohort(s)" depending on the data availability for the selected metric
    for (var i=0; i<this.cohortsList.length; i++) {
      var cohort = this.cohortsList[i];
      // Cohort with data for the selected metric
      if (available_cohorts.includes(cohort) || this.selected_data[cohort]) {
        $('.benchmark_cohort_cb[value="'+cohort+'"]').prop('disabled', false);
        if ($('.benchmark_cohort_cb[value="'+cohort+'"]').parent().attr('title')) {
          $('.benchmark_cohort_cb[value="'+cohort+'"]').parent().removeAttr('title');
        }

        if (this.selected_data[cohort]) {
          // Get list of available groups (Ancestry) for the Cohorts/Metric/Sex selection
          for (var j=0;j<this.selected_data[cohort].length;j++) {
            var anc = this.selected_data[cohort][j].anc;
            if (available_ancestryNames.indexOf(anc) == -1) {
              available_ancestryNames.push(anc);
            }
          }
        }
      }
      // Cohort hasn't data for the selected metric
      else {
        $('.benchmark_cohort_cb[value="'+cohort+'"]').prop('disabled', true);
        var title_text = 'No data available for the cohort '+cohort+' with this performance metric';
        $('.benchmark_cohort_cb[value="'+cohort+'"]').parent().attr('title', title_text);
      }
    }

    // Hide "Ancestry(ies)" not having data for the Cohorts/Metric/Sex selection
    $('.benchmark_ancestry_cb').each(function() {
      var anc = $(this).val();
      if (available_ancestryNames.includes(anc)) {
        $('.benchmark_ancestry_cb[value="'+anc+'"]').parent().show();
      }
      else {
        $('.benchmark_ancestry_cb[value="'+anc+'"]').parent().hide();
      }
    });

    // Hide the "Order by Cohort" option when only 1 Cohort is available/selected
    if (Object.keys(this.selected_data).length == 1) {
      // Set default data ordering before hiding the cohort option
      $('.benchmark_order_by_rb[value="ancestry"]').prop('checked', true);
      this.set_data_ordering();
      $('.benchmark_order_by_rb[value="cohort"]').parent().hide();
    }
    else {
      $('.benchmark_order_by_rb[value="cohort"]').parent().show();
    }

    // Automaticaly check the unique "Cohort" if only 1 option available
    if ($('.benchmark_cohort_cb').not(':disabled').length < 2) {
      $('.benchmark_cohort_cb').not(':disabled').prop('checked', true);
    }

    // Disable "Ancestry(ies)" form if only 1 option available
    if ($('.benchmark_ancestry_cb').parent(':visible').length < 2) {
      $('.benchmark_ancestry_cb').each(function() {
        if ($(this).parent().is(':visible')) {
          $(this).prop('checked', true);
          $(this).attr('disabled', true);
        }
      });
    }
    else {
      $('.benchmark_ancestry_cb').attr('disabled', false);
    }

    // Update the list of 'Cohort - Ancestry' for the sorting
    fill_sorting_form(this.chartData, this.cohorts);
  }

  // Define the PGS list for the X axis
  set_pgs_list() {
    var pgs_list = [];
    // Cohorts
    var cohorts = Object.keys(this.selected_data);
    for (var i=0;i<cohorts.length;i++) {
      var cohort = cohorts[i];
      var data_list = this.selected_data[cohort];
      for (var j=0;j<data_list.length;j++) {
        var pgs_id = data_list[j].pgs;
        var ancestry = data_list[j].anc;
        if (!pgs_list.includes(pgs_id) && this.ancestryNames.includes(ancestry)) {
          pgs_list.push(pgs_id);
        }
      }
    }
    pgs_list.sort();

    this.pgsList = pgs_list;
  }

  // Fetch the selected performance metric
  set_metric() {
    this.metric = $("#benchmark_metric_select option:selected").val();
  }

  // Fetch the selected sex type
  set_sex_type() {
    this.sex_type = $('input[name="benchmark_sex_type"]:checked').val();
  }

  // Fetch the selected data ordering
  set_data_ordering() {
    this.data_ordering = $('input[name="benchmark_order_by"]:checked').val();
  }

  // Fetch the score IDs list and sort them by the selected "Sort by" value
  set_data_sorting() {

    // Set the default list of Score IDs
    this.set_pgs_list();

    this.data_sorting = $("#benchmark_sorting_select option:selected").val();

    var sort_params = this.data_sorting.split('__');
    if (sort_params.length > 1) {
      if (this.pgsList.length > top_list_value) {
        // Show sorting top list filter
        $('#benchmark_sorting_filter_top_list').show();
      }
      else {
        // Hide sorting top list filter
        this.hide_pgs_top_list_filter();
      }
      var cohort = sort_params[0];
      var ancestry = sort_params[1];
      var scores = {};
      for (var i=0;i<this.selected_data[cohort].length;i++) {
        var entry = this.selected_data[cohort][i];
        if (entry.anc == ancestry) {
          scores[entry.pgs] = entry.y;
        }
      }
      var sorted_score_list = this.sort_pgs_list(scores);

      // Update list of category names
      for (var j=0;j<this.pgsList.length;j++) {
        var category = this.pgsList[j];
        if (!sorted_score_list.includes(category)) {
          sorted_score_list.push(category);
        }
      }

      this.pgsList = this.set_pgs_top_list(sorted_score_list);
    }
    else {
      // Hide sorting top list filter
      this.hide_pgs_top_list_filter();
    }
  }

  set_pgs_top_list(score_list) {
    if (score_list.length > top_list_value && $(".benchmark_sorting_filter_top").prop("checked") == true) {
      score_list = score_list.slice(0,top_list_value);
    }
    return score_list;
  }

  // Hide sorting top list filter
  hide_pgs_top_list_filter() {
    $('#benchmark_sorting_filter_top_list').hide();
    $(".benchmark_sorting_filter_top").prop("checked", false);
  }

  // This function updates the chart when an different cohort is selected
  update_cohort() {
    // Fetch selection of cohorts
    this.cohorts = set_cohorts_selection();

    // Remove chart content + legend + X axis + horizontal line + XY axis
    this.remove_chart_main_components(1);
    this.svg.selectAll('.yaxis').remove();
    this.svg.selectAll('.x_label').remove();
    this.svg.selectAll('.y_label').remove();

    // Refresh the forms
    fill_ancestry_form(this.chartData, this.cohorts);
    fill_metric_form(this.chartData, this.cohorts);
    fill_sex_form(this.chartData, this.cohorts);
    fill_sorting_form(this.chartData, this.cohorts);

    // Reset some of the variables
    this.set_metric();
    this.set_sex_type();

    // Reset the data list with the selected datasets
    this.set_selected_data();

    // Reset X axis categories (score IDs list) and sort them
    this.set_data_sorting();

    // Reset groups (ancestries)
    this.ancestryNames = set_ancestryNames();

    // Reset X axis groups (ancestries)
    this.set_cohortAncestryNames();

    // Redraw chart
    this.draw_chart();
  }


  // This function updates the chart when an ancestry is checked in or out
  update_ancestry() {
    // Reset the list of group names (Ancestry)
    this.ancestryNames = set_ancestryNames();

    fill_sorting_form(this.chartData, this.cohorts);

    // Generic update: reset the main variables and redraw the chart
    this.generic_update();
  }


  // This function updates the chart content and Y axis when a different metric is selected
  update_metric() {
    // Change the selected performance metric
    this.set_metric();

    // Update the ancestry and sex type forms
    fill_ancestry_form(this.chartData, this.cohorts);
    fill_sex_form(this.chartData, this.cohorts);
    this.set_sex_type();

    // Reset the data list with the selected datasets
    this.set_selected_data();

    // Reset groups (ancestries)
    this.ancestryNames = set_ancestryNames();

    // Change Y axis label
    this.svg.selectAll('.y_label').remove();
    this.svg.append("text")
        .attr("class", "y_label")
        .attr("font-family", font_family)
        .attr("transform", "rotate(-90)")
        .attr("y", y_label_y)
        .attr("x", 0 - (this.height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text(this.metric);

    // Generic update: reset the main variables and redraw the chart
    this.generic_update();

    resize_select('benchmark_metric_select');
  }


  // This function updates the chart content and Y axis when a different sex is selected
  update_sex() {
    // Change the selected sex type
    this.set_sex_type();

    // Reset the data list with the selected datasets
    this.set_selected_data();

    // Generic update: reset the main variables and redraw the chart
    this.generic_update();
  }


  // This function updates the ordering of the bars/points within a PGS Score
  update_ordering() {
    // Remove chart content + legend + X axis
    this.remove_chart_main_components();

    // Fetch the selected data ordering
    this.set_data_ordering();

    // Reset X axis categories (score IDs list) and sort them
    this.set_data_sorting();

    // X axis groups (ancestries)
    this.set_cohortAncestryNames();

    // The scale for spacing each group's bar:
    //this.set_x0_axis();
    this.set_x1_axis();

    // Redraw X axis
    this.addXAxis();
    // Load updated set of data to the chart
    this.addData();
    // Load updated legend on the chart
    this.addLegend();
  }


  // This function sort of the data (x axis) regarding the values (y axis) for the selected Ancestry/Cohort
  update_sorting() {
    // Remove chart content + legend + X axis
    this.remove_chart_main_components();

    // Reset X axis categories (score IDs list) and sort them
    this.set_data_sorting();

    this.get_min_max_values();

    // (Re)set the axes and scales
    this.set_all_axes();

    // Redraw X axis
    this.addXAxis();
    // Load updated set of data to the chart
    this.addData();
    // Load updated legend on the chart
    this.addLegend();

    resize_select('benchmark_sorting_select');
  }

  // Generic method updating the chart
  generic_update() {
    // Reset X axis groups (ancestries)
    this.set_cohortAncestryNames();

    // Remove chart content + legend + X axis + horizontal line
    this.remove_chart_main_components(1);

    // Reset X axis categories (score IDs list) and sort them
    this.set_data_sorting();

    // Setup the min/max for the Y scale
    this.get_min_max_values();

    // (Re)set the axes and scales
    this.set_all_axes();

    // Redraw X axis
    this.addXAxis();
    // Redraw threshold/horizontal line
    this.addHorizontalLine();
    // Load updated set of data to the chart
    this.addData();
    // Load updated legend on the chart
    this.addLegend();
  }


  // Remove the main components of the chart
  remove_chart_main_components(include_hline) {
    this.svg.selectAll('.chart_content').remove();
    this.svg.selectAll('.chart_legend').remove();
    this.svg.selectAll('.xaxis').remove();
    if (include_hline) {
      this.svg.selectAll('.chart_hline').remove();
    }
  }


  // Get min and max values of the selected dataset
  get_min_max_values() {
    var min_value = '';
    var max_value = '';

    var cohorts = Object.keys(this.selected_data);
    for (var i=0;i<cohorts.length;i++) {
      var cohort = cohorts[i];

      // Min value
      var obj = this;
      var cohort_min_value = d3.min(this.selected_data[cohort], function(d) {
        if (obj.ancestryNames.includes(d.anc) && obj.pgsList.includes(d.pgs)) {
          if ("eb" in d) {
            return (d.eb);
          }
          else {
            return (d.y);
          }
        }
      });
      if (min_value == '' || min_value == undefined || min_value > cohort_min_value) {
        min_value = cohort_min_value;
      }

      // Max value
      var cohort_max_value = d3.max(this.selected_data[cohort], function(d) {
        if (obj.ancestryNames.includes(d.anc) && obj.pgsList.includes(d.pgs)) {
          if ("et" in d) {
            return (d.et);
          }
          else {
            return (d.y);
          }
        }
      });
      if (max_value == '' ||  max_value == undefined || max_value < cohort_max_value) {
        max_value = cohort_max_value;
      }
    }
    var interval = Math.abs(max_value - min_value);
    var interval_extra = (interval/100)*5;
    if (interval_extra == 0) {
      interval_extra = (max_value/100)*5;
    }

    // Min value
    this.min_value = min_value - interval_extra;
    // Max value
    this.max_value = max_value + interval_extra;
  }

  // Sort category list by estimate value
  sort_pgs_list(category_list) {
    var sortedCategories = Object.entries(category_list).sort((a,b) => {
      if(b[1] > a[1]) {
        return 1;
      }
      else if(b[1] < a[1]) {
        return -1;
      }
      else {
        if(a[0] > b[0]) {
          return 1;
        }
        else if(a[0] < b[0]) {
          return -1;
        }
        else {
          return 0;
        }
      }
    });
    return sortedCategories.map(el=>el[0]);
  }

  // Add tooltip on the chart elements
  addTooltip(elem, data) {
    var colour = this.z(data.cohortAncestry);
    var colour_class = 'pgs_benchmark_anc_tooltip_'+colour.replace('#','');

    var data_cohort = data.cohortAncestry.split(sep)[0];

    var shape = this.cohort_data_shapes_html[data_cohort];
    if (shape.includes('shape_triangle') || shape.includes('shape_diamond')) {
      shape += '_alt';
    }

    var title = '<div class="tooltip_content"><div class="tooltip_section"><span class="'+shape+' '+colour_class+'">'+data.anc +'</span> ('+data_cohort+')</div>';
    title += '<div class="tooltip_section">Score ID: <b>'+data.pgs+'</b></div>';
    title += '<div class="tooltip_section">';
    if (data.et) {
      title += '<div>Upper 95: <b>' + data.et + '</b></div><div>Estimate: <b>' + data.y + '</b></div><div>Lower 95: <b>' + data.eb + '</b></div>';
    }
    else {
      title += '<div>Value: <b>' + data.y + '</b></div>';
    }
    title += '</div>';
    title += '<div class="tooltip_section">';
    title += '<div>Sample number: <b>' + data.s_num + '</b>';
    if (data.s_cases) {
      var percent = '';
      if (data.s_cases_p) {
        percent = ' ('+data.s_cases_p+'%)';
      }
      title += '<div>Sample cases: <b>' + data.s_cases + '</b>'+percent;
    }
    if (data.s_ctrls) {
      title += '<div>Sample controls: <b>' + data.s_ctrls + '</b>';
    }
    title += '</div>';
    title += '</div>';
    elem.tooltip({
      'title': title,
      'placement': 'right',
      'html': true
    });
  }


  exportJSON_button() {
    let dataStr = JSON.stringify(this.chartData);
    let dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

    let exportFileDefaultName = 'data.json';

    $('#exportJSON').attr('href', dataUri);
    $('#exportJSON').attr('download', exportFileDefaultName);
  }


  exportCSV_button() {
    // Get the list of distinct metrics
    var metrics_list = [];
    for (var i=0; i<this.cohorts.length; i++) {
      var metrics = Object.keys(this.chartData["data"][this.cohorts[i]]);
      for (var j=0;j<metrics.length;j++) {
        var metric = metrics[j];
        if (!metrics_list.includes(metric)) {
          metrics_list.push(metric);
        }
      }
    }

    var data_csv_list = ['#cohort,ancestry,sex,pgs,'+metrics_list.join()];

    // Restructure the dataset for CSV export
    var cohorts = Object.keys(this.chartData["data"]);
    // Cohorts
    for (var c=0; c<cohorts.length; c++) {
      var cohort = cohorts[c];
      var cohort_data = {};
      // Metrics
      var metrics = Object.keys(this.chartData["data"][cohort]);
      for (var j=0; j<metrics.length; j++) {
        var metric = metrics[j];
        // Sex types
        var sexes = Object.keys(this.chartData["data"][cohort][metric]);
        for (var k=0; k<sexes.length; k++) {
          var sex_type = sexes[k];
          // Entries (PGS ID, Ancestry, data value)
          var entries = this.chartData["data"][cohort][metric][sex_type];
          for (var l=0;l<entries.length;l++) {
            var ancestry = entries[l].anc;
            var pgs_id = entries[l].pgs;
            var data_value = entries[l].y;
            var data_key = ancestry+sep+sex_type+sep+pgs_id;
            if ("eb" in entries[l] && "et" in entries[l]) {
              data_value += ' ['+entries[l].eb+';'+entries[l].et+']';
            }
            // Store data
            if (!Object.keys(cohort_data).includes(data_key)) {
              cohort_data[data_key] = {};
            }
            cohort_data[data_key][metric] = data_value;
          }

        }
      }
      // Generate CSV rows
      var data_keys = Object.keys(cohort_data);
      for (var i=0;i<data_keys.length;i++) {
        var data_key = data_keys[i]
        var data_row = data_key.split(sep);
        data_row.unshift(cohort);
        for (var j=0;j<metrics_list.length;j++) {
          var metric = metrics_list[j];
          var value = '';
          if (cohort_data[data_key][metric]) {
            value = cohort_data[data_key][metric];
          }
          data_row.push(value);
        }
        data_csv_list.push(data_row.join());
      }
    }
    var csv_content = data_csv_list.join("\n");

    var dataUri = 'data:text/csv;charset=utf-8,'+ encodeURIComponent(csv_content);

    var exportFileDefaultName = 'data.csv';

    $('#exportCSV').attr('href', dataUri);
    $('#exportCSV').attr('download', exportFileDefaultName);
  }
}



/*
 * Export buttons events
 */
$( document ).ready(function() {

  $("#exportPDF").on("click", function() {

    console.log("Export PDF");
    svg_xml = (new XMLSerializer()).serializeToString(document.getElementById(svg_id));
    canvas = document.createElement("canvas");
    svgSize = $(svg_xml)[0];
    canvas.width = svgSize.width.baseVal.value;
    canvas.height = svgSize.height.baseVal.value;

    var ctx = canvas.getContext('2d');
    var doc = new jsPDF({ orientation: 'l', unit: 'px', format: [canvas.width,canvas.height] });

    // this is just a JavaScript (HTML) image
    var img = new Image();
    img.src = "data:image/svg+xml;base64," + btoa(svg_xml);
    img.onload = function() {
        // after this, Canvas’ origin-clean is DIRTY
        ctx.drawImage(img, 0, 0);
        doc.addImage(canvas.toDataURL("image/png"), 'PNG', 0, 0);
        doc.save(file_name+'.pdf');
    }
  });

  $("#exportSVG").on("click", function() {
    console.log("Export SVG");
    var serializer = new XMLSerializer();
    var svgData = serializer.serializeToString(document.getElementById(svg_id));
    var svgBlob = new Blob([svgData], {type:"image/svg+xml;charset=utf-8"});
    var svgUrl = URL.createObjectURL(svgBlob);
    var downloadLink = document.createElement("a");
    downloadLink.href = svgUrl;
    downloadLink.download = file_name+'.svg';
    downloadLink.click();
  });

  $("#exportPNG").on("click", function() {
    console.log("Export PNG");
    var svg = d3.select("#"+svg_id);
    var svg_width = svg.node().getBoundingClientRect().width;
    var svg_height = svg.node().getBoundingClientRect().height;
    var svgString = getSVGString(svg.node());
    svgString2Image( svgString, 2*svg_width, 2*svg_height, 'png'); // passes Blob and filesize String to the callback
  });

});



/*
 * Functions that handle actual exporting into PNG
 */
function getSVGString( svgNode ) {
  svgNode.setAttribute('xlink', 'http://www.w3.org/1999/xlink');
  var cssStyleText = getCSSStyles( svgNode );
  appendCSS( cssStyleText, svgNode );

  var serializer = new XMLSerializer();
  var svgString = serializer.serializeToString(svgNode);
  svgString = svgString.replace(/(\w+)?:?xlink=/g, 'xmlns:xlink='); // Fix root xlink without namespace
  svgString = svgString.replace(/NS\d+:href/g, 'xlink:href'); // Safari NS namespace fix

  return svgString;

  // Extract CSS styling
  function getCSSStyles( parentElement ) {
    var selectorTextArr = [];

    // Add Parent element Id and Classes to the list
    selectorTextArr.push( '#'+parentElement.id );
    for (var c = 0; c < parentElement.classList.length; c++) {
      if ( !contains('.'+parentElement.classList[c], selectorTextArr) ) {
        selectorTextArr.push( '.'+parentElement.classList[c] );
      }
    }

    // Add Children element Ids and Classes to the list
    var nodes = parentElement.getElementsByTagName("*");
    for (var i = 0; i < nodes.length; i++) {
      var id = nodes[i].id;
      if ( !contains('#'+id, selectorTextArr) ) {
        selectorTextArr.push( '#'+id );
      }

      var classes = nodes[i].classList;
      for (var c = 0; c < classes.length; c++) {
        if ( !contains('.'+classes[c], selectorTextArr) ) {
          selectorTextArr.push( '.'+classes[c] );
        }
      }
    }

    // Extract CSS Rules
    var extractedCSSText = "";
    for (var i = 0; i < document.styleSheets.length; i++) {
      var s = document.styleSheets[i];
      try {
        if(!s.cssRules) continue;
      } catch( e ) {
        if(e.name !== 'SecurityError') throw e; // for Firefox
        continue;
      }

      var cssRules = s.cssRules;
      for (var r = 0; r < cssRules.length; r++) {
        if ( contains( cssRules[r].selectorText, selectorTextArr ) ) {
          extractedCSSText += cssRules[r].cssText;
        }
      }
    }
    return extractedCSSText;

    function contains(str,arr) {
      return arr.indexOf( str ) === -1 ? false : true;
    }
  }

  function appendCSS( cssText, element ) {
    var styleElement = document.createElement("style");
    styleElement.setAttribute("type","text/css");
    styleElement.innerHTML = cssText;
    var refNode = element.hasChildNodes() ? element.children[0] : null;
    element.insertBefore( styleElement, refNode );
  }
}

function svgString2Image( svgString, width, height, format) {

  var imgsrc = 'data:image/svg+xml;base64,'+ btoa( unescape( encodeURIComponent( svgString ) ) ); // Convert SVG string to data URL

  var canvas = document.createElement("canvas");
  var context = canvas.getContext("2d");

  canvas.width = width;
  canvas.height = height;

  var image = new Image();
  image.onload = function() {
    context.clearRect ( 0, 0, width, height );
    context.drawImage(image, 0, 0, width, height);

    canvas.toBlob( function(blob) {
      saveAs( blob, file_name+'.'+format );
    });
  };
  image.src = imgsrc;
}



/*
 * Functions to fill and fetch the forms:
 * Cohort, Ancestry, Metric
 */

// Build "Cohort" form
function fill_cohort_form(data) {
  $("#benchmark_cohort_list").html('');
  var html_cb = '';
  var cohort_length = data.cohorts.length;
  for (var i=0; i<cohort_length;i++) {
    id = 'cohort_'+i;
    var cohort = data.cohorts[i];
    var cohort_shape = chart_shapes_html[i];

    html_cb += '<div>'+
               '  <input type="checkbox" class="benchmark_cohort_cb" checked value="'+cohort+'" id="'+id+'">'+
               '  <label class="mb-0" for="'+id+'"> '+cohort+' (<span class="'+cohort_shape+'"></span>)</label>'+
               '</div>';
  }
  $("#benchmark_cohort_list").append(html_cb);
}


// Build "Ancestry" form
function fill_ancestry_form(data, cohorts) {
  var previous_unselected = [];
  $(".benchmark_ancestry_cb").each(function () {
    if ($(this).prop("checked") == false)  {
      previous_unselected.push($(this).val());
    }
  });

  $("#benchmark_ancestry_list").html('');
  var tmp_ancestry_list = [];
  var ancestry_ordered_list = [];
  var html_cb = '';
  // Cohorts
  for (var i=0; i<cohorts.length;i++) {
    var cohort = cohorts[i];
    var cohort_ancestry_list = data.ancestries[cohort];
    // Get distinct ancestries
    for (var j=0; j<cohort_ancestry_list.length;j++) {
      var ancestry = cohort_ancestry_list[j];
      if (!tmp_ancestry_list.includes(ancestry)) {
        tmp_ancestry_list.push(ancestry);
        var anc_order = data.ancestry_groups.indexOf(ancestry);
        ancestry_ordered_list.push( {'order': anc_order, 'value': ancestry} );
      }
    }
  }
  // Order the ancestries, matching the order in 'ancestry_groups'
  var ancestry_list = [];
  ancestry_ordered_list = ancestry_ordered_list.sort(function(a, b){ return a.order - b.order; });
  for (var k=0; k<ancestry_ordered_list.length;k++) {
    ancestry_list.push(ancestry_ordered_list[k].value);
  }

  // Generate HTML checkboxes
  var extra_colour = 0;
  for (var l=0; l<ancestry_list.length;l++) {
    id = 'gpName_'+l;
    var ancestry = ancestry_list[l];
    var colour = '';
    if (ancestry_colours[ancestry]) {
      colour = ancestry_colours[ancestry];
    }
    else {
      colour = chart_colours[extra_colour];
      extra_colour++;
    }
    var is_checked = ' checked';
    if (previous_unselected.includes(ancestry)) {
      is_checked = '';
    }
    var is_disabled = '';
    if (ancestry_list.length == 1) {
      is_disabled = ' disabled';
    }
    var cb_class = 'pgs_benchmark_anc_'+colour.replace('#','');
    html_cb += '<div>'+
               '  <input type="checkbox" class="benchmark_ancestry_cb"'+is_checked+is_disabled+' value="'+ancestry+'" id="'+id+'">'+
               '  <label class="mb-0" for="'+id+'"> '+ancestry+' (<span class="'+cb_class+'"></span>)</label>'+
               '</div>';
  }
  $("#benchmark_ancestry_list").append(html_cb);
}


// Build "Performance Metric" form
function fill_metric_form(data, cohorts) {

  var previous_selection = $("#benchmark_metric_select option:selected").val();

  $("#benchmark_metric_select").html('');
  var metrics_list = [];
  // Cohorts - fetch metrics
  for (var i=0; i<cohorts.length;i++) {
    var cohort = cohorts[i];
    var metrics = Object.keys(data.data[cohort]);
    for (var j=0; j<metrics.length;j++) {
      var metric = metrics[j];
      if (!metrics_list.includes(metric)) {
        if (metric == 'Odds Ratio') {
          metrics_list.unshift(metric);
        }
        else {
          metrics_list.push(metric);
        }
      }
    }
  }
  // Fill the form
  for (var k=0; k<metrics_list.length;k++) {
    var metric = metrics_list[k];
    var option = new Option(metric, metric);
    if (previous_selection && metric == previous_selection) {
      option = new Option(metric, metric, true, true);
    }
    $("#benchmark_metric_select").append(option);
  }

  resize_select('benchmark_metric_select');
}


// Build "Sex" form
function fill_sex_form(data, cohorts) {

  var previous_selection = $('input[name="benchmark_sex_type"]:checked').val();
  var metric = $("#benchmark_metric_select option:selected").val();

  $("#benchmark_sex_list").html('');
  var sex_list = [];
  var html_rb = '';
  // Cohorts - fetch sexes
  for (var i=0; i<cohorts.length;i++) {
    var cohort = cohorts[i];
    var cohort_sex_list = data.sexes[cohort];
    // List sexes from the selected metric
    if (metric in data.data[cohort]) {
      // Sexes
      for (var j=0; j<cohort_sex_list.length;j++) {
        var sex_type = cohort_sex_list[j];
        if (!sex_list.includes(sex_type) && sex_type in data.data[cohort][metric]) {
          sex_list.push(sex_type);
        }
      }
    }
  }

  // Setup the radio button selected by default
  var entry_to_check = sex_list[0];
  if (previous_selection && sex_list.includes(previous_selection)) {
    entry_to_check = previous_selection;
  }

  // Generate HTML radio buttons
  for (var k=0; k<sex_list.length;k++) {
    id = 'sex_type_'+k;
    var sex_type = sex_list[k];
    var is_checked = '';
    if (entry_to_check == sex_type) {
      is_checked = ' checked';
    }
    html_rb += '<div>'+
               '  <input type="radio" name="benchmark_sex_type" class="benchmark_sex_type_rb"'+is_checked+' value="'+sex_type+'" id="'+id+'">'+
               '  <label class="mb-0" for="'+id+'"> '+sex_type+'</label>'+
               '</div>';
  }
  $("#benchmark_sex_list").append(html_rb);
}


// Build "Performance Metric" form
function fill_sorting_form(data, cohorts) {

  var previous_selection = $("#benchmark_sorting_select option:selected").val();

  $("#benchmark_sorting_select").html('');
  var sorting_list = {};
  // Cohorts - fetch metrics
  for (var i=0; i<cohorts.length;i++) {
    var cohort = cohorts[i];
    var cohort_ancestry_list = data.ancestries[cohort];
    if (!$('.benchmark_cohort_cb[value="'+cohort+'"]').prop('disabled') &&
        $('.benchmark_cohort_cb[value="'+cohort+'"]').prop('checked')) {
      var cohort_shape = chart_shapes_html[i];
      // Ancestries
      for (var j=0; j<cohort_ancestry_list.length;j++) {
        var ancestry = cohort_ancestry_list[j];
        if ($('.benchmark_ancestry_cb[value="'+ancestry+'"]').is(':visible') &&
            $('.benchmark_ancestry_cb[value="'+ancestry+'"]').prop('checked')) {
          if (!sorting_list[cohort]) {
            sorting_list[cohort] = [];
          }
          sorting_list[cohort].push(ancestry);
        }
      }
    }
  }
  // Fill the form
  var option = new Option('Polygenic Score ID','Polygenic Score ID');
  $("#benchmark_sorting_select").append(option);
  $.each( sorting_list, function( cohort, ancestries ) {
    var grp_option = $('<optgroup/>').attr('label', cohort);
    for (var k=0; k<ancestries.length;k++) {
      var ancestry = ancestries[k];
      var value = cohort+sep+ancestry;
      var label = ancestry+' ('+cohort+')';
      var option = new Option(label,value);
      if (previous_selection && value == previous_selection) {
        option = new Option(label,value, true, true);
      }
      grp_option.append(option);
    }
    $("#benchmark_sorting_select").append(grp_option);
  });

  // Select Top 10 form
  var sorting_form_val = $("#benchmark_sorting_select option:selected").val();
  var sort_params = sorting_form_val.split('__');
  if (sort_params.length == 1) {
    $("#benchmark_sorting_filter_top_list").hide();
    $(".benchmark_sorting_filter_top").prop('checked', false);
  }

  resize_select('benchmark_sorting_select');
}


// Set the list of cohorts
function set_cohortsList() {
  var c_list = [];
  $(".benchmark_cohort_cb").each(function () {
    c_list.push($(this).val());
  });
  return c_list;
}

// Set the list of selected cohorts
function set_cohorts_selection() {
  var c_list = [];
  $(".benchmark_cohort_cb").not(":disabled").each(function () {
    if ($(this).prop("checked")) {
      c_list.push($(this).val());
    }
  });
  return c_list;
}

// Set the list of distinct groups (ancestry)
function set_ancestryNames() {
  var gp_list = [];
  $(".benchmark_ancestry_cb").each(function () {
    if ($(this).prop("checked"))  {
      gp_list.push($(this).val());
    }
  });
  return gp_list;
}

// Resize the select dropdown field to match the current selection
function resize_select(id){
  select_id = '#'+id;
  $('body').append('<select id="width_tmp_select" style="display:none"><option id="width_tmp_option"></option></select>');
  $("#width_tmp_option").html($(select_id+' option:selected').text());
  $(select_id).width($("#width_tmp_select").width());
}
