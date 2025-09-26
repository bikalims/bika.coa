window.d3 = d3

class TimeSeries 

  ###*
   * TimeSeries Field for the Listing Table
   *
   * A multi value field is identified by the column type "timeseries" in the
   * listing view, e.g.  `self.columns = {"Result": {"type": "timeseries"}, ... }`
   *
  ###
  constructor: (config) ->
    @container = config.container  # DOM element
    @state = config.state
    @props = config.props
    # console.log('constructor complete')

  ###
   * Converts the string value to an array
  ###
  to_matrix: (list, headers) ->
    # No values yet
    return [] if list.length == 0

    # Map each inner list to an object using the headers
    matrix = list.map (innerList) ->
        obj = {}
        headers.forEach (header, index) ->
            obj[header] = innerList[index]
        obj

    matrix.map (row) ->
        headers.forEach (header, index) ->
            if index = 0
              row[header] = row[header]
            else
              row[header] = parseFloat(row[header])
    matrix


  getLineConfigs = (count) ->
    configs = [
      {symbol: d3.symbolStar, dash: ""}
      {symbol: d3.symbolSquare, dash: ""}
      {symbol: d3.symbolTriangle, dash: ""}
      {symbol: d3.symbolDiamond, dash: ""}
      {symbol: d3.symbolCross, dash: ""}
    ]
    configs.slice(0, count)

  # Create symbol generator
  symbolGenerator = d3.symbol().size(48)  # Adjust size as needed

  ###
   * Inputs table builder. Generates a table of  inputs as matrix
  ###
  build_graph: ->
    # console.log "TimeSeries::build_graph: entered"
    try
      # console.log("Data being used for rendering:", this.state.value)  # Log the data
      values = this.state.value

      if values == ""
        console.log "TimeSeries::build_graph: exit because no data"
        @container.current.appendChild([])
        return

      # console.log 'Graph raw data: ' + values
      # Get datasets
      columns = this.props.item.time_series_columns
      visible_cols = (c for c in columns when c.ColumnHide != 'on')
      if visible_cols.length == 0
        return
      col_types = visible_cols.map (i) -> i.ColumnType
      col_colors = visible_cols.map (i) -> i.ColumnColor
      headers = visible_cols.map (i) -> i.ColumnTitle
      # console.log 'Graph headers: ' + headers
      index = headers[0]

      err_col = ""
      err_key = ""
      error_columns = (c for c in columns when c.ColumnType == 'errorbar')
      if error_columns.length == 1
        err_col = error_columns[0]
        err_key = error_columns[0].ColumnTitle
      avg_col = ""
      avg_key = ""
      avg_columns = (c for c in columns when c.ColumnType == 'average')
      if avg_columns.length == 1
          avg_col = avg_columns[0]
          avg_key = avg_columns[0].ColumnTitle
      legend_headers = (c.ColumnTitle for c in columns when c.ColumnHide != 'on' and c.ColumnType != 'errorbar').slice(1)

      visible_idxs = (i for c, i in columns when c.ColumnHide != 'on')
      visible_values = values.map (row) ->
         (row[i] for i in visible_idxs)
      # console.log 'visible_values: ' + JSON.stringify(visible_values)

      data = @to_matrix(visible_values, headers, 'graph')
      # console.log 'data: ' + JSON.stringify(data)

      # Generate the line colors (exclude index)
      line_configs = getLineConfigs(headers.length - 1)

      # Set up dimensions
      margin = {top: 40, right: 80, bottom: 50, left: 60}
      width = 700 - margin.left - margin.right
      height = 400 - margin.top - margin.bottom + 50

      # Set up scales
      xScale = d3.scaleLinear()
        .domain(d3.extent(data, (d) -> parseFloat(d[index])))
        .range([0, width])

      # Set up Y scale with trimmed domain
      maxError = 0
      if err_key
        maxError = d3.max(data.flatMap((row) -> parseFloat(row[err_key])))

      absoluteMinY = d3.min(data.flatMap((row) -> legend_headers.map((header) -> parseFloat(row[header]))))
      absoluteMinY -= maxError
      if absoluteMinY == 0
        minY = -0.5
      else if absoluteMinY > 0
        minY = absoluteMinY * 0.95
      else
        minY = absoluteMinY * 1.05

      maxY = d3.max(data.flatMap((row) -> legend_headers.map((header) -> parseFloat(row[header]))))
      maxY += maxError

      # console.log('minY: ' + minY + ' maxY: ' + maxY + " height: " + height)
      yScale = d3.scaleLinear()
        .domain([minY, maxY])
        .nice()  # expands domain to "nice" human-friendly values
        .range([height, 0])

      # Create SVG container
      y_offset = 140
      svg = d3.select(@container)
        .append('svg')
        .attr("id", "timeseries-svg")  # Add unique ID
        .style("height", "#{height+y_offset}px")

      # Remove any previous SVG content
      svg.selectAll('*').remove()

      svg_height = height + margin.top + margin.bottom
      # console.log('svg_height: ' + svg_height)
      svg = svg
        .attr("width", width + margin.left + margin.right)
        .attr("height", svg_height)
        .attr('xmlns', 'http://www.w3.org/2000/svg')
        .append("g")
        .attr("transform", "translate(#{margin.left},#{margin.top})")

      # Graph title
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", -margin.top / 2)
        .attr("text-anchor", "middle")
        .style("font-size", "16px")
        .style("font-weight", "bold")
        .text(this.props.item.time_series_graph_title)

      # X-axis label
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text(this.props.item.time_series_graph_xaxis)

      # Y-axis label
      svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -margin.left + 15)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .text(this.props.item.time_series_graph_yaxis)

      # y-axis horizontal grid lines
      svg.append("g")
        .attr("class", "grid horizontal")
        .call(
          d3.axisLeft(yScale)
            .tickSize(-width)  # Extend ticks across the chart width
        )
        .selectAll("line")
        .style("stroke", "#999")  # Lighter gray
        .style("stroke-dasharray", "2,2")
        .style("opacity", 0.8)       # Adjust transparency

      # Add vertical grid lines
      # console.log('height: ' + height)
      svg.append("g")
        .attr("class", "grid vertical")
        .attr("transform", "translate(0, #{height})")
        .call(
          d3.axisBottom(xScale)
            .tickSize(-height)  # Extend ticks across the chart height
        )
        .selectAll("line")
        .style("stroke", "#999")  # Lighter gray
        .style("stroke-dasharray", "2,2")
        .style("opacity", 0.8)       # Adjust transparency


      # Get interpolation
      interp = this.props.item.time_series_graph_interpolation
      # console.log(interp)
      curve_val = d3[interp]

      headers.slice(1).forEach((key, i) ->
        line_configs_idx = i % line_configs.length
        # console.info "Main loop: " + key + "  " + i

        # Filter data to exclude rows with null, undefined, or non-numeric values for the current key
        filteredData = data.filter (d) ->
          d[index]? and d[key]? and d[index] isnt "" and d[key] isnt "" and \
          not (typeof d[index] isnt 'string' and (d[index] is null or isNaN(d[index]))) and \
          not (typeof d[key] isnt 'string' and (d[key] is null or isNaN(d[key])))
        # console.log 'filteredData: ' + JSON.stringify(filteredData)

        # Line generator
        lineGen = d3.line()
          .curve(curve_val)
          .x((d) ->
            xScale(d[index])
          )
          .y((d) ->
            yScale(d[key])
          )

        if key != err_key
          svg.append("path")
            .datum(filteredData) # Use filtered data
            .attr("fill", "none")
            .attr("stroke-width", 2)
            .attr("stroke", col_colors[i+1])
            .attr("stroke-dasharray", line_configs[line_configs_idx].dash)
            .attr("d", lineGen)

          # Add data points with different symbols
          svg.selectAll(".symbol-#{i}")
            .data(filteredData) # Use filtered data
            .enter().append("path")
            .attr("class", "symbol symbol-#{i}")
            .attr("d", symbolGenerator.type(line_configs[line_configs_idx].symbol))
            .attr("transform", (d) ->
              # Ensure valid x and y before applying transform
              xVal = parseFloat(d[index])
              yVal = parseFloat(d[key])
              if not isNaN(xVal) and not isNaN(yVal)
                "translate(#{xScale(xVal)}, #{yScale(yVal)})"
              else
                null # Skip invalid points
            )
            .style("fill", col_colors[i+1])
        else
          svg.selectAll(".error-bar")
            .data(filteredData)
            .enter()
            .append("line")
            .attr("class", "error-bar")
            .attr "x1", (d) -> xScale(d[index])
            .attr "x2", (d) -> xScale(d[index])
            .attr "y1", (d) -> yScale(d[avg_key] - d[err_key])
            .attr "y2", (d) -> yScale(d[avg_key] + d[err_key])
            .attr "stroke", avg_col.ColumnColor
            .attr "stroke-width", 1

          # Caps
          capWidth = 0.5

          # Top cap
          svg.selectAll(".error-cap-top")
            .data(filteredData)
            .enter()
            .append("line")
            .attr("class", "error-cap-top")
            .attr "x1", (d) -> xScale(d[index] - capWidth/2)
            .attr "x2", (d) -> xScale(d[index] + capWidth/2)
            .attr "y1", (d) -> yScale(d[avg_key] + d[err_key])
            .attr "y2", (d) -> yScale(d[avg_key] + d[err_key])
            .attr "stroke", avg_col.ColumnColor
            .attr "stroke-width", 1

          # Bottom cap
          svg.selectAll(".error-cap-bottom")
            .data(filteredData)
            .enter()
            .append("line")
            .attr("class", "error-cap-bottom")
            .attr "x1", (d) -> xScale(d[index] - capWidth/2)
            .attr "x2", (d) -> xScale(d[index] + capWidth/2)
            .attr "y1", (d) -> yScale(d[avg_key] - d[err_key])
            .attr "y2", (d) -> yScale(d[avg_key] - d[err_key])
            .attr "stroke", avg_col.ColumnColor
            .attr "stroke-width", 1
      )

      # Add legend
      legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(50, #{height + 50})")  # Move legend below the graph

      # Add legend items
      legendItems = legend.selectAll("g")
        .data(legend_headers)
        .enter().append("g")
        .attr("transform", (d, i) ->
          xOffset = parseFloat((i % Math.floor(width / 100)) * 100)  # Horizontal spacing
          yOffset = parseFloat(Math.floor(i / Math.floor(width / 100)) * 20)  # Vertical spacing
          "translate(#{xOffset}, #{yOffset})"
        )

      # Add legend color symbols
      legendItems.append("path")
        .attr("d", (d, i) ->
          line_configs_idx = i % line_configs.length
          d3.symbol().type(line_configs[line_configs_idx].symbol).size(100)()
        )
        .attr("transform", "translate(9, 9)")  # Center the symbol within the legend item
        .style("fill", (d, i) -> col_colors[i+1])

      # Add legend text
      legendItems.append("text")
        .attr("x", 24)
        .attr("y", 9)
        .attr("dy", "0.35em")
        .style("font-size", "12px")
        .text((d) -> d)

      console.log "TimeSeries::build_graph: ended"

    catch error
      console.error("Error in build_graph:", error)

window.TimeSeries = TimeSeries
