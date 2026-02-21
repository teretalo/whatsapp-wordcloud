"""Who is writing the most?"""
import streamlit as st
import plotly.graph_objects as go
from collections import defaultdict, Counter
from datetime import timedelta

st.set_page_config(page_title="Speakers Analysis", page_icon="👥", layout="wide")

st.title("👥 Who is writing the most?")
st.markdown("Analyze each person's activity and contribution patterns in your WhatsApp conversations.")

# Check if chat is uploaded
if not st.session_state.get('chat_uploaded', False):
    st.warning("⚠️ No chat data loaded. Please upload a chat file on the Home page first.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Get data from session state
speakers = st.session_state.speakers
message_dates = st.session_state.message_dates

# We need to get speaker data with dates - need to update this
# For now, check if we have the necessary data
if 'speaker_timeline_data' not in st.session_state:
    st.error("Speaker timeline data not available. Please re-upload your chat on the Home page.")
    st.stop()

speaker_timeline_data = st.session_state.speaker_timeline_data

if speakers and speaker_timeline_data:
    # Dropdown for metric selection
    metric_type = st.selectbox(
        "Select metric to display",
        options=["Messages", "Words"],
        index=0
    )

    st.divider()

    # Doughnut chart showing distribution
    st.subheader(f"📊 Distribution by {metric_type}")

    # Calculate totals for each speaker
    speaker_totals = {}
    for speaker, data in speaker_timeline_data.items():
        if metric_type == "Messages":
            speaker_totals[speaker] = len(data)
        else:  # Words
            speaker_totals[speaker] = sum(word_count for _, _, word_count in data)

    # Sort speakers by total
    sorted_speakers = sorted(speaker_totals.items(), key=lambda x: x[1], reverse=True)

    # Prepare data for doughnut chart
    names = [s[0] for s in sorted_speakers]
    values = [s[1] for s in sorted_speakers]
    total = sum(values)
    percentages = [f"{(v/total*100):.1f}%" for v in values]

    # Create doughnut chart with consistent colors
    speaker_colors = st.session_state.get('speaker_colors', {})
    chart_colors = [speaker_colors.get(name, '#667eea') for name in names]

    fig_donut = go.Figure(data=[go.Pie(
        labels=names,
        values=values,
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>' +
                      f'{metric_type}: %{{value:,}}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>',
        textinfo='label+percent',
        textposition='outside',
        marker=dict(colors=chart_colors)
    )])

    fig_donut.update_layout(
        showlegend=True,
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=40, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        annotations=[dict(
            text=f'Total<br>{total:,}<br>{metric_type.lower()}',
            x=0.5, y=0.5,
            font_size=16,
            font_color='#1f2937',
            showarrow=False
        )]
    )

    st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # Timeline section
    st.subheader(f"📈 Activity Over Time")

    # Get timeline data for all speakers
    # speaker_timeline_data should be: {speaker: [(date, message, word_count), ...]}

    # Determine aggregation based on conversation duration
    all_dates = [date for speaker_data in speaker_timeline_data.values() for date, _, _ in speaker_data]
    if all_dates:
        sorted_dates = sorted(all_dates)
        duration = (sorted_dates[-1] - sorted_dates[0]).days
        aggregation_type = "Weekly" if duration < 365 else "Monthly"

        # Create consistent timeline for ALL speakers based on overall conversation range
        if duration < 365:
            # Weekly timeline
            first_week = sorted_dates[0] - timedelta(days=sorted_dates[0].weekday())
            last_week = sorted_dates[-1] - timedelta(days=sorted_dates[-1].weekday())

            all_weeks = []
            current = first_week
            while current <= last_week:
                all_weeks.append(current)
                current += timedelta(days=7)

            timeline_dates = all_weeks
        else:
            # Monthly timeline
            from datetime import datetime
            start_year, start_month = sorted_dates[0].year, sorted_dates[0].month
            end_year, end_month = sorted_dates[-1].year, sorted_dates[-1].month

            all_months = []
            year, month = start_year, start_month
            while (year, month) <= (end_year, end_month):
                all_months.append((year, month))
                month += 1
                if month > 12:
                    month = 1
                    year += 1

            timeline_dates = [datetime(year, month, 1) for year, month in all_months]
            timeline_month_keys = all_months

        # Aggregate data by speaker
        fig = go.Figure()

        # Get consistent color mapping
        speaker_colors = st.session_state.get('speaker_colors', {})

        for speaker, data in speaker_timeline_data.items():
            # Aggregate by week or month using the consistent timeline
            if duration < 365:
                # Weekly aggregation
                week_data = defaultdict(lambda: {'messages': 0, 'words': 0})
                for date, message, word_count in data:
                    week_start = date - timedelta(days=date.weekday())
                    week_data[week_start]['messages'] += 1
                    week_data[week_start]['words'] += word_count

                # Use consistent timeline for all speakers
                if metric_type == "Messages":
                    counts = [week_data[date]['messages'] for date in timeline_dates]
                else:
                    counts = [week_data[date]['words'] for date in timeline_dates]

            else:
                # Monthly aggregation
                month_data = defaultdict(lambda: {'messages': 0, 'words': 0})
                for date, message, word_count in data:
                    month_key = (date.year, date.month)
                    month_data[month_key]['messages'] += 1
                    month_data[month_key]['words'] += word_count

                # Use consistent timeline for all speakers
                if metric_type == "Messages":
                    counts = [month_data[month_key]['messages'] for month_key in timeline_month_keys]
                else:
                    counts = [month_data[month_key]['words'] for month_key in timeline_month_keys]

            dates = timeline_dates

            # Add trace for this speaker with consistent color
            color = speaker_colors.get(speaker, '#667eea')
            fig.add_trace(go.Scatter(
                x=dates,
                y=counts,
                mode='lines+markers',
                name=speaker,
                line=dict(color=color, width=2),
                marker=dict(size=4),
                hovertemplate=f'<b>{speaker}</b><br>%{{x}}<br>{metric_type}: %{{y}}<extra></extra>'
            ))

        # Update layout
        y_axis_title = "Number of Messages" if metric_type == "Messages" else "Number of Words"
        fig.update_layout(
            title=dict(
                text=f'{aggregation_type} Activity by Speaker - {metric_type}',
                font=dict(size=20, color='#1f2937')
            ),
            xaxis=dict(
                title='Time',
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)',
                zeroline=False
            ),
            yaxis=dict(
                title=y_axis_title,
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)',
                zeroline=False
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            height=500,
            margin=dict(l=60, r=40, t=80, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    # Message Types Analysis
    if 'speaker_message_types' in st.session_state and st.session_state.speaker_message_types:
        st.divider()

        st.subheader("📊 Message Types Analysis")

        # Dropdown for message type selection
        message_type_options = {
            'link': '🔗 Links',
            'media': '📸 Media (images, videos, voice messages, documents, stickers, GIFs)',
            'emoji': '😊 Emojis'
        }

        # Short labels for center annotation
        annotation_labels = {
            'link': 'links',
            'media': 'media',
            'emoji': 'emojis'
        }

        selected_type = st.selectbox(
            "Select message type to analyze",
            options=list(message_type_options.keys()),
            format_func=lambda x: message_type_options[x],
            index=0
        )

        # Get counts for selected type
        speaker_message_types = st.session_state.speaker_message_types
        type_counts = {}
        for speaker, types in speaker_message_types.items():
            count = types.get(selected_type, 0)
            if count > 0:
                type_counts[speaker] = count

        if type_counts:
            # Sort by count
            sorted_speakers = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            names = [s[0] for s in sorted_speakers]
            values = [s[1] for s in sorted_speakers]
            total = sum(values)

            # Create doughnut chart with consistent colors
            speaker_colors = st.session_state.get('speaker_colors', {})
            chart_colors = [speaker_colors.get(name, '#667eea') for name in names]

            fig_types = go.Figure(data=[go.Pie(
                labels=names,
                values=values,
                hole=0.4,
                hovertemplate='<b>%{label}</b><br>' +
                              message_type_options[selected_type] + ': %{value:,}<br>' +
                              'Percentage: %{percent}<br>' +
                              '<extra></extra>',
                textinfo='label+percent',
                textposition='outside',
                marker=dict(colors=chart_colors)
            )])

            fig_types.update_layout(
                showlegend=True,
                height=450,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=40, t=40, b=60),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                annotations=[dict(
                    text=f'Total<br>{total:,}<br>{annotation_labels[selected_type]}',
                    x=0.5, y=0.5,
                    font_size=16,
                    font_color='#1f2937',
                    showarrow=False
                )]
            )

            st.plotly_chart(fig_types, use_container_width=True)

            # Show top 3
            st.markdown("**Top Contributors:**")
            for idx, (speaker, count) in enumerate(sorted_speakers[:3], 1):
                percentage = (count / total * 100)
                st.write(f"{idx}. **{speaker}**: {count:,} ({percentage:.1f}%)")

        else:
            st.info(f"No {annotation_labels[selected_type]} found in this conversation.")

        # Show top emojis per person if emoji type is selected
        if selected_type == 'emoji' and 'speaker_emojis' in st.session_state:
            st.divider()
            st.subheader("🏆 Top 5 Emojis by Person")

            speaker_emojis = st.session_state.speaker_emojis
            from collections import Counter

            # Get top speakers by emoji count
            emoji_totals = {speaker: len(emojis) for speaker, emojis in speaker_emojis.items()}
            top_speakers = sorted(emoji_totals.items(), key=lambda x: x[1], reverse=True)[:5]

            if top_speakers:
                cols = st.columns(min(len(top_speakers), 3))

                for idx, (speaker, total_count) in enumerate(top_speakers):
                    with cols[idx % 3]:
                        st.markdown(f"**{speaker}** ({total_count} total)")

                        # Count emoji frequency
                        emoji_counts = Counter(speaker_emojis[speaker])
                        top_5_emojis = emoji_counts.most_common(5)

                        # Display as a nice list
                        for emoji, count in top_5_emojis:
                            percentage = (count / total_count * 100)
                            st.write(f"{emoji} × {count} ({percentage:.1f}%)")
            else:
                st.info("No emoji data available.")

    # Who Initiates section
    if 'speaker_initiations' in st.session_state and st.session_state.speaker_initiations:
        st.divider()

        st.subheader("💬 Who Initiates Conversations")
        st.caption("📝 *Note: An initiation is counted when someone sends the first message after 12+ hours of silence.*")

        speaker_initiations = st.session_state.speaker_initiations
        initiation_timeline_data = st.session_state.initiation_timeline_data

        # Sort by initiation count
        sorted_initiations = sorted(speaker_initiations.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sorted_initiations]
        values = [s[1] for s in sorted_initiations]
        total_initiations = sum(values)

        # Create doughnut chart with consistent colors
        speaker_colors = st.session_state.get('speaker_colors', {})
        chart_colors = [speaker_colors.get(name, '#667eea') for name in names]

        fig_init = go.Figure(data=[go.Pie(
            labels=names,
            values=values,
            hole=0.4,
            hovertemplate='<b>%{label}</b><br>' +
                          'Initiations: %{value:,}<br>' +
                          'Percentage: %{percent}<br>' +
                          '<extra></extra>',
            textinfo='label+percent',
            textposition='outside',
            marker=dict(colors=chart_colors)
        )])

        fig_init.update_layout(
            showlegend=True,
            height=450,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=40, t=40, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            annotations=[dict(
                text=f'Total<br>{total_initiations:,}<br>initiations',
                x=0.5, y=0.5,
                font_size=16,
                font_color='#1f2937',
                showarrow=False
            )]
        )

        st.plotly_chart(fig_init, use_container_width=True)

        # Show top 3
        st.markdown("**Most Frequent Initiators:**")
        for idx, (speaker, count) in enumerate(sorted_initiations[:3], 1):
            percentage = (count / total_initiations * 100)
            st.write(f"{idx}. **{speaker}**: {count:,} initiations ({percentage:.1f}%)")

        # Timeline of initiations
        st.divider()
        st.subheader("📈 Initiation Activity Over Time")

        # Get all initiation dates
        all_initiation_dates = [date for dates in initiation_timeline_data.values() for date in dates]

        if all_initiation_dates:
            sorted_dates = sorted(all_initiation_dates)
            duration = (sorted_dates[-1] - sorted_dates[0]).days
            aggregation_type = "Weekly" if duration < 365 else "Monthly"

            # Create consistent timeline
            if duration < 365:
                # Weekly timeline
                first_week = sorted_dates[0] - timedelta(days=sorted_dates[0].weekday())
                last_week = sorted_dates[-1] - timedelta(days=sorted_dates[-1].weekday())

                all_weeks = []
                current = first_week
                while current <= last_week:
                    all_weeks.append(current)
                    current += timedelta(days=7)

                timeline_dates = all_weeks
            else:
                # Monthly timeline
                from datetime import datetime
                start_year, start_month = sorted_dates[0].year, sorted_dates[0].month
                end_year, end_month = sorted_dates[-1].year, sorted_dates[-1].month

                all_months = []
                year, month = start_year, start_month
                while (year, month) <= (end_year, end_month):
                    all_months.append((year, month))
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1

                timeline_dates = [datetime(year, month, 1) for year, month in all_months]
                timeline_month_keys = all_months

            # Create figure
            fig_init_timeline = go.Figure()

            # Get consistent color mapping
            speaker_colors = st.session_state.get('speaker_colors', {})

            for speaker, dates in initiation_timeline_data.items():
                # Aggregate by week or month
                if duration < 365:
                    # Weekly aggregation
                    week_data = defaultdict(int)
                    for date in dates:
                        week_start = date - timedelta(days=date.weekday())
                        week_data[week_start] += 1

                    counts = [week_data[date] for date in timeline_dates]
                else:
                    # Monthly aggregation
                    month_data = defaultdict(int)
                    for date in dates:
                        month_key = (date.year, date.month)
                        month_data[month_key] += 1

                    counts = [month_data[month_key] for month_key in timeline_month_keys]

                # Add trace with consistent color
                color = speaker_colors.get(speaker, '#667eea')
                fig_init_timeline.add_trace(go.Scatter(
                    x=timeline_dates,
                    y=counts,
                    mode='lines+markers',
                    name=speaker,
                    line=dict(color=color, width=2),
                    marker=dict(size=4),
                    hovertemplate=f'<b>{speaker}</b><br>%{{x}}<br>Initiations: %{{y}}<extra></extra>'
                ))

            # Update layout
            fig_init_timeline.update_layout(
                title=dict(
                    text=f'{aggregation_type} Conversation Initiations by Speaker',
                    font=dict(size=20, color='#1f2937')
                ),
                xaxis=dict(
                    title='Time',
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.05)',
                    zeroline=False
                ),
                yaxis=dict(
                    title='Number of Initiations',
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.05)',
                    zeroline=False
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                hovermode='x unified',
                height=500,
                margin=dict(l=60, r=40, t=80, b=60),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )

            st.plotly_chart(fig_init_timeline, use_container_width=True)

else:
    st.info("No speaker data available. Upload a chat file that includes speaker names.")
    if st.button("← Go to Home"):
        st.switch_page("app.py")
