Extending *Let's Go! Trains*
============================

*Let's Go! Trains* is a pure Python 3 GTK 3.0 application designed for extensibility. New components of the following
types can be added by installing additional Python packages defining `entry points
<https://packaging.python.org/specifications/entry-points/>`_:

* track pieces (``letsgo.piece``)
* controllers (``letsgo.controller``)
* sensors (``letsgo.sensor``)
* layout parsers (``letsgo.layout_parser``)
* layout serializers (``letsgo.layout_serializer``)

Creating a new track piece
--------------------------

Track pieces are all subclasses of :py:class:`letsgo.pieces.Piece`.

Overview of a track piece
~~~~~~~~~~~~~~~~~~~~~~~~~

A track piece is a collection of *anchors*, i.e. points at which they can be connected to other track pieces to form a
logical network of track. There is a primary (first) anchor, and each anchor is positioned relative to that anchor.

Another method provides information to any routeing engine about which traversals are possible from any given anchor.
For example, it is impossible to traverse between adjacent anchors on a crossover piece.

Extending existing types of pieces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Let's Go! Trains* have base implementations for straight, curve and points pieces, which you can extend quite simply if
you need another variant of those. For example, a quarter curve would look like:

.. code-block:: python

   from letsgo.pieces.curve import BaseCurve

   class QuarterCurve(BaseCurve):
       radius = 40
       per_circle = 64
       sleepers = 1
       label = "quarter-curve"


Minimal implementation
~~~~~~~~~~~~~~~~~~~~~~

Let's try to implement a double crossover:

.. code-block:: python

   from typing import Dict, Tuple

   from letsgo.pieces import Piece


   class DoubleCrossoverPiece(Piece):
       anchor_names = ('in-left', 'out-left', 'in-right', 'out-right')

       crossover_length = 56  # this is a guess

       def __init__(self, *, state_in='left', state_out='left', **kwargs):
           self.state_in = state_in
           self.state_out = state_out
           super().__init__(**kwargs)

       def bounds(self):
           return Bounds(x=0, y=-4, width=48, height=24)

       def traversals(self, anchor_from: str) -> Dict[str, Tuple[float, bool]]:
           if anchor_from == 'in-left':
               return {
                   'out-left': (48, self.state_in == 'left'),
                   'out-right': (self.crossover_length, self.state_in == 'right'),
               }
           elif anchor_from == 'in-right':
               ...

       def relative_positions(self):
           return {
               **super().relative_positions(),
               'in-right': Position(0, 16, math.pi),
               'out-left': Position(48, 0, 0),
               'out-right': Position(48, 16, 0),
          }

       def point_position(self, in_anchor, offset, out_anchor=None):
           if in_anchor == 'in-left' and out_anchor == 'out-left':
               return Position(0, offset, 0)
           elif in_anchor == 'in-right' and out_anchor == 'out-right':
               return Position(16, offset, 0)
           elif in_anchor == 'in-left' and out_anchor == 'out-right':
               ...  # probably some maths with Beziers and differentiation to calculate
                    # the point and angle on the crossover path
           ...

       def draw(self, cr: cairo.Context, drawing_options: DrawingOptions):
           ...  # draw the piece using cairo here


Creating a new controller
-------------------------

Controllers are components that either connect *Let's Go! Trains* to the outside world, or which wire together
components within *Let's Go! Trains*.

The application comes with four :ref:`built-in controllers <automation>`:
