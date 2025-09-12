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
  to_matrix: (listString, headers) ->
    # No values yet
    return [] if !listString || listString.length == 0

    # Parse the string version of the list of lists into an array
    # list = JSON.parse(listString)
    list = listString

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

      # Get datasets
      columns = this.props.item.time_series_columns
      col_types = columns.map (i) -> i.ColumnType
      col_colors = columns.map (i) -> i.ColumnColor
      headers = columns.map (i) -> i.ColumnTitle
      index = headers[0]
      data = @to_matrix(values, headers)

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
      absoluteMinY = d3.min(data.flatMap((row) -> headers.slice(1).map((header) -> parseFloat(row[header]))))
      if absoluteMinY > 0
        minY = absoluteMinY * 0.95
      else
        minY = absoluteMinY * 1.05

      maxY = d3.max(data.flatMap((row) -> headers.slice(1).map((header) -> parseFloat(row[header]))))

      console.log('minY: ' + minY + ' maxY: ' + maxY + " height: " + height)
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
      console.log('svg_height: ' + svg_height)
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
        console.info "Main loop: " + key + "  " + i

        # Filter data to exclude rows with null, undefined, or non-numeric values for the current key
        validData = data.filter((d) ->
          d[key]? and not isNaN(d[key]) # Ensure value exists and is numeric
        )

        # Line generator
        lineGen = d3.line()
          .curve(curve_val)
          .x((d) ->
            xScale(d[index])
          )
          .y((d) ->
            yScale(d[key])
          )

        svg.append("path")
          .datum(validData) # Use filtered data
          .attr("fill", "none")
          .attr("stroke-width", 2)
          .attr("stroke", col_colors[i+1])
          .attr("stroke-dasharray", line_configs[line_configs_idx].dash)
          .attr("d", lineGen)

        # Add data points with different symbols
        svg.selectAll(".symbol-#{i}")
          .data(validData) # Use filtered data
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
      )

      # Add legend
      legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(50, #{height + 50})")  # Move legend below the graph

      # Add legend items
      legendItems = legend.selectAll("g")
        .data(headers.slice(1))
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
