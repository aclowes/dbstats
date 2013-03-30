import json
import time
import pytz

from datetime import datetime, timedelta
from django.db.models import Count, Avg
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from dbstats.databases import get_wrapper
from dbstats.models import Server, Database, SqlStatement, SqlActivity

def home(request):
    servers = Server.objects.all()
    for server in servers:
        server.database_count = server.database_set.count() + 2
    return render(request, 'home.html', {
        'page': 'home',
        'user': request.user,
        'servers': servers,
    })


def activity(request, database_id):
    database = get_object_or_404(Database, id=database_id)
    # TODO paginate
    queries = SqlStatement.objects.filter(database=database).annotate(
        num_queries=Count('sqlactivity'),
        avg_duration=Avg('sqlactivity__duration')
    ).order_by('-num_queries')[:15]

    return render(request, 'activity.html', {
        'page': 'activity',
        'user': request.user,
        'database': database,
        'queries': queries,
    })


def activity_graph(request, database_id):
    """
    Returns JSON representing recent activity for a given database
    The response is a list of dict, each counting the number of queries of each type running at the time
    TODO: match this with DB stats like index hits/misses, row fetches to deduce expensive queries
    [ {"start": 1351750328000, "1": 1, "2": 0}, ...]
    """
    database = get_object_or_404(Database, id=database_id)
    statements = database.sqlstatement_set.values_list('id', flat=True)
    activities = SqlActivity.objects.filter(statement_id__in=statements)
    start = stop = datetime.utcnow().replace(tzinfo=pytz.UTC)
    data = [None]
    for activity in activities:
        index = int((activity.start - start).total_seconds()) / 10
        if index < 0:
            # create more slots in the beginning
            data[0:0] = [None] * -index
            start += timedelta(seconds=index)
            index = 0

        # insert the start data
        period = data[index]
        if not period:
            period = data[index] = {'start': start + timedelta(seconds=index)}
        period.setdefault(activity.statement_id, 0)
        period[activity.statement_id] += 1

        # insert the stop data
        index += int(activity.duration) / 10000 + 1
        period = data[index]
        if not period:
            period = data[index] = {'start': start + timedelta(seconds=index)}
        period.setdefault(activity.statement_id, 0)
        period[activity.statement_id] -= 1

    clean_data = []
    running_totals = dict([(id, 0) for id in statements])
    for period in data:
        # JavaScript unix time is in milliseconds, multiply by 1000
        if period:
            running_totals = running_totals.copy()
            running_totals['start'] = int(time.mktime(period['start'].timetuple()) * 1000)
            for id in statements:
                running_totals[id] += period.get(id, 0)
            clean_data.append(running_totals)

    data = json.dumps(clean_data)
    return HttpResponse(data, content_type='application/json')


def explain(request, statement_id):
    statement = get_object_or_404(SqlStatement, id=statement_id)
    server = statement.database.server
    server.type = 'postgres'
    statement.explain = get_wrapper(server).explain(statement.statement)
    return render(request, 'explain.html', {
        'page': 'explain',
        'user': request.user,
        'server': server,
        'statement': statement,
    })


def settings(request, server_id=None):
    server = get_object_or_404(Server, id=server_id)
    server.type = 'postgres'
    server.settings = get_wrapper(server).get_settings()

    return render(request, 'settings.html', {
        'page': 'activity',
        'user': request.user,
        'server': server,
    })
