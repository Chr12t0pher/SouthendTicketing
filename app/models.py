from app import db


class Games(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team = db.Column(db.String(64))
    code = db.Column(db.String(8))
    date = db.Column(db.Date)
    east_stand = db.Column(db.Boolean, default=True)
    south_stand = db.Column(db.Boolean, default=True)
    west_stand = db.Column(db.Boolean, default=True)
    x_block = db.Column(db.Boolean, default=False)
    yz_block = db.Column(db.Boolean, default=False)
    stats = db.relationship("Stats", backref="games", lazy="dynamic")


class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    time = db.Column(db.DateTime)
    total_sold = db.Column(db.Integer)
    total_available = db.Column(db.Integer)

